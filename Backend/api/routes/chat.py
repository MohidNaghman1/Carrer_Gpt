# api/routes/chat.py
import json
from fastapi import APIRouter, HTTPException, status, Depends,UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
from Backend import db
from sqlalchemy.orm import Session
from services import chat_service
# Import models, schemas, and the db session dependency
from db import models, schemas
from db.database import get_db
# Import our new dependency
from api.dependencies import get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("/{session_id}/messages", response_model=schemas.Message)
def post_new_message(
    session_id: int, 
    message: schemas.MessageCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
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

@router.post("/", response_model=schemas.ChatSession, status_code=status.HTTP_201_CREATED)
def create_new_chat_session(
    session_data: schemas.ChatSessionCreate,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Creates a new chat session AND processes the first message if provided.
    """
    new_title = session_data.title
    if session_data.first_message:
        first_few_words = " ".join(session_data.first_message.split()[:4])
        new_title = f"{first_few_words}..." if len(session_data.first_message.split()) > 4 else session_data.first_message

    # 1. Create the session object
    db_session = models.ChatSession(title=new_title, user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # --- THIS IS THE CRITICAL FIX ---
    # 2. If a first message was provided, process it immediately
    if session_data.first_message:
        chat_service.process_user_message(
            db_session=db,
            chat_session=db_session,
            user_prompt=session_data.first_message
        )
        db.refresh(db_session)

    return db_session
@router.get("/", response_model=List[schemas.ChatSession])
def get_all_user_sessions(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # <-- PROTECT
):
    """
    Retrieves all chat sessions for the current logged-in user.
    """
    # Filter sessions by the logged-in user's ID
    sessions = db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).all()
    return sessions

@router.get("/{session_id}", response_model=schemas.ChatSession)
def get_chat_session(
    session_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # <-- PROTECT
):
    """
    Retrieves the details for a specific chat session, ensuring it belongs to the user.
    """

    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # CRITICAL: Check if the session belongs to the logged-in user
    if db_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    return db_session

@router.put("/{session_id}", response_model=schemas.ChatSession)
def update_chat_session(
    session_id: int,
    payload: schemas.ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
    db_session.title = payload.title
    db.commit()
    db.refresh(db_session)
    return db_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
    # Deleting the session will cascade to messages due to ORM config
    db.delete(db_session)
    db.commit()
    return

@router.post("/{session_id}/messages", response_model=schemas.Message)
def post_new_message(
    session_id: int, 
    message: schemas.MessageCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # <-- PROTECT
):
    """
    Adds a new message to a session, ensuring it belongs to the user.
    """
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    
    # Combine the checks for existence and ownership
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found or not authorized")

    db_user_message = models.ChatMessage(
        session_id=session_id, role="human", content=message.content
    )
    db.add(db_user_message)
    
    db_ai_message = models.ChatMessage(
        session_id=session_id, role="ai", content=f"Dummy response to: '{message.content}'"
    )
    db.add(db_ai_message)
    
    db.commit()
    db.refresh(db_ai_message)
    
    return db_ai_message


@router.post("/resume-analysis", response_model=schemas.ChatSession, status_code=status.HTTP_201_CREATED)
async def create_session_with_resume_analysis( # <-- ADD async
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Create a new session with a smart title
    db_session = models.ChatSession(title=f"Resume Analysis: {resume.filename}", user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    
    # Your service function is synchronous, which is fine to call from an async endpoint.
    # FastAPI is smart enough to run it in a thread pool.
    chat_service.process_resume_file(db, db_session, resume.file)

    db.refresh(db_session) # Refresh again to load the new messages

    return db_session

# This endpoint adds a resume analysis to an EXISTING session
@router.post("/{session_id}/resume-analysis", response_model=schemas.Message)
async def add_resume_analysis_to_session(
    session_id: int,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
    
    chat_service.process_resume_file(db, db_session, resume.file)

    # Return the latest AI message (the analysis)
    latest_ai_message = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session_id,
        models.ChatMessage.role == 'ai'
    ).order_by(models.ChatMessage.timestamp.desc()).first()

    return latest_ai_message


@router.post("/{session_id}/messages/stream")
def post_new_message_stream(
    session_id: int,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id).first()
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
            print(f"Error during stream: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")