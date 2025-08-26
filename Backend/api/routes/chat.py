# api/routes/chat.py
import json
import logging
import traceback
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session
from fastapi.concurrency import run_in_threadpool
from services import chat_service
# Import models, schemas, and the db session dependency
from db import models, schemas
from db.database import get_db
# Import our new dependency
from api.dependencies import get_current_user

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

@router.post("/", response_model=schemas.ChatSession, status_code=status.HTTP_201_CREATED)
def create_new_chat_session(
    session_data: schemas.ChatSessionCreate,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Creates a new chat session AND processes the first message if provided.
    """
    try:
        new_title = session_data.title
        if session_data.first_message:
            first_few_words = " ".join(session_data.first_message.split()[:4])
            new_title = f"{first_few_words}..." if len(session_data.first_message.split()) > 4 else session_data.first_message

        # 1. Create the session object with keyword arguments
        db_session = models.ChatSession(
            title=new_title, 
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        # 2. If a first message was provided, process it immediately
        if session_data.first_message:
            chat_service.process_user_message(
                db_session=db,
                chat_session=db_session,
                user_prompt=session_data.first_message
            )
            db.refresh(db_session)

        return db_session
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.get("/", response_model=List[schemas.ChatSession])
def get_all_user_sessions(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves all chat sessions for the current logged-in user.
    """
    try:
        # Filter sessions by the logged-in user's ID
        sessions = db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).all()
        return sessions
    except Exception as e:
        logger.error(f"Error retrieving user sessions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving sessions")

@router.get("/{session_id}", response_model=schemas.ChatSession)
def get_chat_session(
    session_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves the details for a specific chat session, ensuring it belongs to the user.
    """
    try:
        db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if db_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # CRITICAL: Check if the session belongs to the logged-in user
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        return db_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving session")

@router.put("/{session_id}", response_model=schemas.ChatSession)
def update_chat_session(
    session_id: int,
    payload: schemas.ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if not db_session or db_session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
        
        db_session.title = payload.title
        db.commit()
        db.refresh(db_session)
        return db_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat session {session_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating session")

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if not db_session or db_session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
        
        # Deleting the session will cascade to messages due to ORM config
        db.delete(db_session)
        db.commit()
        return
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session {session_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting session")

@router.post("/{session_id}/messages", response_model=schemas.Message)
def post_new_message(
    session_id: int, 
    message: schemas.MessageCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Adds a new message to a session and gets AI response.
    """
    try:
        db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        
        if not db_session or db_session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")

        # CALL THE REAL AI SERVICE
        chat_service.process_user_message(
            db_session=db,
            chat_session=db_session,
            user_prompt=message.content
        )

        # Retrieve the latest AI message to return it
        latest_ai_message = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id,
            models.ChatMessage.role == 'ai'
        ).order_by(models.ChatMessage.timestamp.desc()).first()

        if not latest_ai_message:
            raise HTTPException(status_code=500, detail="Could not retrieve AI response.")

        return latest_ai_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail="Error processing message")

@router.post("/{session_id}/messages/stream")
def post_new_message_stream(
    session_id: int,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        db_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id, 
            models.ChatSession.user_id == current_user.id
        ).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")

        def event_generator():
            try:
                for token in chat_service.process_user_message_stream(
                    db_session=db,
                    chat_session=db_session,
                    user_prompt=message.content
                ):
                    # SSE format: data: {"token": "your token here"}\n\n
                    yield f"data: {json.dumps({'token': token})}\n\n"
                # Signal the end of the stream
                yield f"data: {json.dumps({'event': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"Error during stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up stream for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Error setting up message stream")

@router.post("/resume-analysis", response_model=schemas.ChatSession, status_code=status.HTTP_201_CREATED)
async def create_session_with_resume_analysis(
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new chat session with resume analysis"""
    logger.info(f"Creating resume analysis session for user {current_user.id}")
    
    try:
        # Validate file
        if not resume.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Check file type
        allowed_types = [
            'application/pdf', 
            'text/plain', 
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if resume.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {resume.content_type}. Allowed types: PDF, TXT, DOC, DOCX"
            )

        # Check file size (10MB limit)
        if resume.size and resume.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large. Maximum 10MB allowed.")

        # Create new chat session with explicit keyword arguments
        new_chat_session = models.ChatSession(
            user_id=current_user.id,
            title=f"Resume Analysis - {resume.filename}",
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Created ChatSession object for user {current_user.id}")
        
        db.add(new_chat_session)
        db.commit()
        db.refresh(new_chat_session)
        
        logger.info(f"Saved ChatSession to database with ID {new_chat_session.id}")

        # Process resume file in thread pool
        try:
            await run_in_threadpool(
                chat_service.process_resume_file,
                db_session=db,
                chat_session=new_chat_session,
                file_stream=resume.file
            )
            logger.info(f"Successfully processed resume for session {new_chat_session.id}")
        except Exception as process_error:
            logger.error(f"Error processing resume: {process_error}")
            logger.error(traceback.format_exc())
            # Clean up the session if processing fails
            db.delete(new_chat_session)
            db.commit()
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing resume file: {str(process_error)}"
            )
        
        db.refresh(new_chat_session)
        logger.info(f"Successfully created session {new_chat_session.id}")
        return new_chat_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_session_with_resume_analysis: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/{session_id}/resume-analysis", response_model=schemas.Message)
async def add_resume_analysis_to_session(
    session_id: int,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add resume analysis to an existing session"""
    logger.info(f"Adding resume analysis to session {session_id} for user {current_user.id}")
    
    try:
        # Validate file
        if not resume.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Check file type
        allowed_types = [
            'application/pdf', 
            'text/plain', 
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if resume.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {resume.content_type}. Allowed types: PDF, TXT, DOC, DOCX"
            )

        # Retrieve and verify chat session
        chat_session_obj = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == current_user.id
        ).first()
        
        if not chat_session_obj:
            raise HTTPException(
                status_code=404, 
                detail="Chat session not found or not authorized"
            )
        
        logger.info(f"Found chat session {session_id}")

        # Process resume file
        try:
            await run_in_threadpool(
                chat_service.process_resume_file,
                db_session=db,
                chat_session=chat_session_obj,
                file_stream=resume.file
            )
            logger.info(f"Successfully processed resume for session {session_id}")
        except Exception as process_error:
            logger.error(f"Error processing resume: {process_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing resume file: {str(process_error)}"
            )
        
        # Get the latest AI message
        latest_ai_message = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id,
            models.ChatMessage.role == 'ai'
        ).order_by(models.ChatMessage.timestamp.desc()).first()
        
        if not latest_ai_message:
            raise HTTPException(
                status_code=500, 
                detail="Could not retrieve AI response after processing resume"
            )
            
        logger.info(f"Successfully added resume analysis to session {session_id}")
        return latest_ai_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in add_resume_analysis_to_session: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )