# api/routes/chat.py
import json
import traceback
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi.concurrency import run_in_threadpool
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

# Add CORS headers manually to responses if needed
def add_cors_headers(response: JSONResponse, origin: str = "*"):
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Add OPTIONS handler for preflight requests
@router.options("/{path:path}")
async def options_handler(request: Request):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "https://carrer-gpt.vercel.app",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@router.post("/", response_model=schemas.ChatSession, status_code=status.HTTP_201_CREATED)
async def create_new_chat_session(
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

        # 1. Create the session object
        db_session = models.ChatSession(title=new_title, user_id=current_user.id)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        # 2. If a first message was provided, process it immediately
        if session_data.first_message:
            try:
                await run_in_threadpool(
                    chat_service.process_user_message,
                    db_session=db,
                    chat_session=db_session,
                    user_prompt=session_data.first_message
                )
                db.refresh(db_session)
            except Exception as e:
                print(f"Error processing first message: {e}")
                traceback.print_exc()
                # Don't fail the session creation, just log the error
                
        response = JSONResponse(content=schemas.ChatSession.from_orm(db_session).model_dump(mode='json'))
        return add_cors_headers(response, "https://carrer-gpt.vercel.app")
        
    except Exception as e:
        print(f"Error creating chat session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")

@router.post("/resume-analysis", response_model=schemas.ChatSession, status_code=status.HTTP_201_CREATED)
async def create_session_with_resume_analysis(
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # 1. Create the session
        new_chat_session = models.ChatSession(
            title=f"Resume Analysis: {resume.filename}", 
            user_id=current_user.id
        )
        db.add(new_chat_session)
        db.commit()
        db.refresh(new_chat_session)

        # 2. Read the file bytes
        file_bytes = await resume.read()
        
        # 3. Call the service in a threadpool with the correct arguments
        await run_in_threadpool(
            chat_service.process_resume_file, 
            chat_session_id=new_chat_session.id,
            file_bytes=file_bytes,
            filename=resume.filename
        )
        
        db.refresh(new_chat_session)
        response = JSONResponse(content=schemas.ChatSession.from_orm(new_chat_session).model_dump(mode='json'))
        return add_cors_headers(response, "https://carrer-gpt.vercel.app")
        
    except Exception as e:
        print(f"Error in resume analysis: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {str(e)}")

@router.post("/{session_id}/resume-analysis", response_model=schemas.ChatSession)
async def add_resume_analysis_to_session(
    session_id: int,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        chat_session_obj = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id, 
            models.ChatSession.user_id == current_user.id
        ).first()
        
        if not chat_session_obj:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        file_bytes = await resume.read()

        await run_in_threadpool(
            chat_service.process_resume_file, 
            chat_session_id=chat_session_obj.id,
            file_bytes=file_bytes,
            filename=resume.filename
        )
        
        db.refresh(chat_session_obj)
        response = JSONResponse(content=schemas.ChatSession.from_orm(chat_session_obj).model_dump(mode='json'))
        return add_cors_headers(response, "https://carrer-gpt.vercel.app")
        
    except Exception as e:
        print(f"Error adding resume to session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to add resume: {str(e)}")

@router.get("/", response_model=List[schemas.ChatSession])
async def get_all_user_sessions(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves all chat sessions for the current logged-in user.
    """
    try:
        sessions = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == current_user.id
        ).all()
        response = JSONResponse(content=[schemas.ChatSession.from_orm(s).model_dump(mode='json') for s in sessions])
        return add_cors_headers(response, "https://carrer-gpt.vercel.app")
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@router.get("/{session_id}", response_model=schemas.ChatSession)
async def get_chat_session(
    session_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieves the details for a specific chat session, ensuring it belongs to the user.
    """
    try:
        db_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id
        ).first()
        
        if db_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        if db_session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        response = JSONResponse(content=schemas.ChatSession.from_orm(db_session).model_dump(mode='json'))
        return add_cors_headers(response, "https://carrer-gpt.vercel.app")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching session {session_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")

@router.post("/{session_id}/messages/stream")
async def post_new_message_stream(
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
                yield f"data: [DONE]\n\n"
            except Exception as e:
                print(f"Error during stream: {e}")
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
        return StreamingResponse(
            event_generator(), 
            media_type="text/event-stream",
            headers={
                "Access-Control-Allow-Origin": "https://carrer-gpt.vercel.app",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in stream endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

@router.put("/{session_id}", response_model=schemas.ChatSession)
async def update_chat_session(
    session_id: int,
    payload: schemas.ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        db_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id
        ).first()
        
        if not db_session or db_session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
            
        db_session.title = payload.title
        db.commit()
        db.refresh(db_session)
        
        response = JSONResponse(content=schemas.ChatSession.from_orm(db_session).model_dump(mode='json'))
        return add_cors_headers(response, "https://carrer-gpt.vercel.app")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        db_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id
        ).first()
        
        if not db_session or db_session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat session not found or not authorized")
            
        db.delete(db_session)
        db.commit()
        
        return JSONResponse(
            content={},
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "https://carrer-gpt.vercel.app",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting session: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

# Debug endpoint to test CORS
@router.get("/debug/cors")
async def cors_debug():
    return JSONResponse(
        content={"message": "CORS is working from chat router"},
        headers={
            "Access-Control-Allow-Origin": "https://carrer-gpt.vercel.app",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )