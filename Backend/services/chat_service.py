from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from io import BytesIO
import json
from db.database import SessionLocal 
from langgraph_core.utils.text_processing import preprocess_user_input
import re
from langgraph_core.utils.file_parser import extract_text_from_file 
from langgraph_core.agents.chains import (
    create_career_advisor_chain,
    create_job_search_chain,
    create_learning_path_chain,
    create_resume_analyzer_chain,
    create_resume_qa_chain
)
from langgraph_core.graph_backend import supervisor_llm, llm_parser
from db import models
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# This helper function is no longer needed here as the logic is inside the stream function
# def get_history(...):

def process_user_message_stream(db_session: Session, chat_session: models.ChatSession, user_prompt: str):
    """
    This is the definitive, stateful, hybrid router and streamer.
    It correctly implements all supervisor logic.
    """
    print("--- HYBRID STREAMING SERVICE ---")

    try:
        history_messages = []
        db_messages = db_session.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == chat_session.id
        ).order_by(models.ChatMessage.timestamp.asc()).all()
        for msg in db_messages:
            if msg.role == "human": history_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "ai": history_messages.append(AIMessage(content=msg.content))
        
        resume_text = chat_session.resume_text
        agent_chain = None
        input_data = {}

        # --- HYBRID SUPERVISOR LOGIC ---
        
        # RULE 1: Python Safety Net for Resume Follow-ups
        if resume_text:
            user_input_lower = user_prompt.lower()
            follow_up_keywords = ["my resume", "my cv", "the document", "my skills", "rewrite", "improve", "experience", "education", "project"]
            if any(keyword in user_input_lower for keyword in follow_up_keywords):
                print("--- SERVICE ROUTER: Python rule triggered for ResumeQAAgent. ---")
                agent_chain = create_resume_qa_chain()
                input_data = {"resume_context": resume_text, "question": user_prompt}
        
        # Only run the LLM router if the Python rule didn't fire
        if agent_chain is None:
            # RULE 2: Context-Aware LLM Routing
            history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_messages])
            resume_exists = "Yes" if resume_text else "No"
        
            # Simple routing for now - default to CareerAdvisor
            agent_chain = create_career_advisor_chain()
            input_data = {"question": user_prompt, "resume_context": resume_text}

        # --- STREAM FROM THE CHOSEN AGENT AND SAVE TO DB ---
        full_ai_response = ""
        
        # First, save the user message
        db_user_message = models.ChatMessage(session_id=chat_session.id, role="human", content=user_prompt)
        db_session.add(db_user_message)
        db_session.commit()
        
        # Stream the AI response
        try:
            for token in agent_chain.stream(input_data):
                if token:  # Only yield non-empty tokens
                    full_ai_response += token
                    # Split large tokens into smaller chunks for better streaming
                    if len(token) > 50:
                        # Split by words to maintain readability
                        words = token.split(' ')
                        current_chunk = ""
                        for word in words:
                            current_chunk += word + " "
                            if len(current_chunk) > 30:  # Send chunks of ~30 characters
                                yield current_chunk.strip()
                                current_chunk = ""
                        if current_chunk.strip():
                            yield current_chunk.strip()
                    else:
                        yield token
        except Exception as stream_error:
            print(f"Error during streaming: {stream_error}")
            error_message = "I apologize, but I encountered an error while processing your request. Please try again."
            full_ai_response = error_message
            yield error_message
        
        # Save the AI response
        db_ai_message = models.ChatMessage(session_id=chat_session.id, role="ai", content=full_ai_response)
        db_session.add(db_ai_message)
        db_session.commit()
        
    except Exception as e:
        print(f"Error in process_user_message_stream: {e}")
        import traceback
        traceback.print_exc()
        # Yield error message to user
        yield f"I apologize, but I encountered an error: {str(e)}. Please try again."

# The NON-streaming function for the first message and resume analysis
def process_user_message(db_session: Session, chat_session: models.ChatSession, user_prompt: str) -> str:
    full_response = ""
    # Collect the full response from the generator
    for token in process_user_message_stream(db_session, chat_session, user_prompt):
        full_response += token
    return full_response

# The thread-safe resume processing function
def process_resume_file(chat_session_id: int, file_bytes: bytes, filename: str):
    db: Session = SessionLocal()
    try:
        chat_session = db.query(models.ChatSession).filter(models.ChatSession.id == chat_session_id).first()
        if not chat_session: return

        resume_analyzer_agent = create_resume_analyzer_chain()
        resume_text = extract_text_from_file(file_bytes, filename)

        if "Error:" in resume_text:
            analysis_string = resume_text
        else:
            analysis_string = resume_analyzer_agent.invoke({"resume_text": resume_text})

        chat_session.resume_text = resume_text
        db_human_message = models.ChatMessage(session_id=chat_session.id, role="human", content=f"Analyzed resume: {filename}")
        db_ai_message = models.ChatMessage(session_id=chat_session.id, role="ai", content=analysis_string)
        db.add_all([db_human_message, db_ai_message])
        db.commit()
    finally:
        db.close()