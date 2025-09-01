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
    It correctly implements all supervisor logic with proper agent routing.
    """
    print("--- HYBRID STREAMING SERVICE ---")

    try:
        # Get chat history
        history_messages = []
        db_messages = db_session.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == chat_session.id
        ).order_by(models.ChatMessage.timestamp.asc()).all()
        for msg in db_messages:
            if msg.role == "human": 
                history_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "ai": 
                history_messages.append(AIMessage(content=msg.content))
        
        resume_text = chat_session.resume_text
        agent_chain = None
        input_data = {}

        # --- SUPERVISOR-BASED AGENT ROUTING ---
        
        # Use the intelligent supervisor from graph_backend instead of hardcoded routing
        from langgraph_core.graph_backend import supervisor_node
        
        # Create a mock state for the supervisor
        mock_state = {
            "messages": history_messages + [HumanMessage(content=user_prompt)],
            "resume_text": resume_text,
            "file_data": None
        }
        
        try:
            # Get supervisor decision
            supervisor_decision = supervisor_node(mock_state)
            next_agent = supervisor_decision.get("next", "CareerAdvisor")
            print(f"--- SUPERVISOR DECISION: Routing to {next_agent} ---")
            
            # Route to appropriate agent based on supervisor decision
            if next_agent == "ResumeQAAgent" and resume_text:
                agent_chain = create_resume_qa_chain()
                input_data = {"resume_context": resume_text, "question": user_prompt}
            elif next_agent == "LearningPath":
                agent_chain = create_learning_path_chain()
                input_data = {"question": user_prompt, "resume_context": resume_text}
            elif next_agent == "JobSearch":
                agent_chain = create_job_search_chain()
                input_data = {"question": user_prompt, "resume_context": resume_text}
            elif next_agent == "ResumeAnalyst":
                # For resume analysis requests, use career advisor as fallback
                print("--- SUPERVISOR: ResumeAnalyst requested but not implemented in chat. Using CareerAdvisor. ---")
                agent_chain = create_career_advisor_chain()
                input_data = {"question": user_prompt, "resume_context": resume_text}
            else:
                # Default to Career Advisor for general career guidance
                agent_chain = create_career_advisor_chain()
                input_data = {"question": user_prompt, "resume_context": resume_text}
                
        except Exception as supervisor_error:
            print(f"--- SUPERVISOR ERROR: {supervisor_error}. Defaulting to CareerAdvisor. ---")
            agent_chain = create_career_advisor_chain()
            input_data = {"question": user_prompt, "resume_context": resume_text}

        # --- STREAM FROM THE CHOSEN AGENT AND SAVE TO DB ---
        full_ai_response = ""
        
        # Prepare messages to save (we'll save them all at once at the end)
        db_user_message = models.ChatMessage(session_id=chat_session.id, role="human", content=user_prompt)
        db_ai_message = None  # Will be created after streaming
        
        # Stream the AI response
        try:
            for token in agent_chain.stream(input_data):
                if token and token.strip():  # Only yield non-empty tokens
                    full_ai_response += token
                    # Improved streaming: yield tokens more naturally
                    # Only split very long tokens (>100 chars) to maintain good streaming
                    if len(token) > 100:
                        # Split by sentences or words for very long tokens
                        import re
                        sentences = re.split(r'([.!?]+)', token)
                        current_chunk = ""
                        for sentence in sentences:
                            current_chunk += sentence
                            if len(current_chunk) > 80:  # Send chunks of ~80 characters
                                yield current_chunk
                                current_chunk = ""
                        if current_chunk.strip():
                            yield current_chunk
                    else:
                        # Most tokens are fine as-is for good streaming
                        yield token
        except Exception as stream_error:
            print(f"Error during streaming: {stream_error}")
            error_message = "I apologize, but I encountered an error while processing your request. Please try again."
            full_ai_response = error_message
            yield error_message

        # Create and save both messages at once
        db_ai_message = models.ChatMessage(session_id=chat_session.id, role="ai", content=full_ai_response)
        db_session.add_all([db_user_message, db_ai_message])
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