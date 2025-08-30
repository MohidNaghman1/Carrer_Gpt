from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from io import BytesIO
import json
from db.database import SessionLocal 

from langgraph_core.utils.file_parser import extract_text_from_file 
# Import the chain CREATION functions and agents, not the compiled app
from langgraph_core.agents.chains import (
    create_career_advisor_chain,
    create_job_search_chain,
    create_learning_path_chain,
    create_resume_analyzer_chain,
    create_resume_qa_chain
)
from langgraph_core.graph_backend import supervisor_llm, llm_parser # We need the supervisor's LLM
from db import models
# Re-create the supervisor chain here for manual routing
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- This is a simplified supervisor just for routing ---
# (You can copy the full prompt from your graph_backend.py for consistency)
supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI routing specialist. Your only job is to analyze the user's message and output exactly ONE word from this list: `ResumeAnalyst`, `CareerAdvisor`, `LearningPath`, `JobSearch`, `ResumeQAAgent`, `END`."),
    ("user", "User request: '{request}'\n\nRouting decision:")
])
supervisor_chain = supervisor_prompt | supervisor_llm | StrOutputParser()
# --- End of simplified supervisor ---


def get_history(db_session: Session, chat_session: models.ChatSession, user_prompt: str):
    """Helper function to reconstruct message history."""
    db_messages = db_session.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == chat_session.id
    ).order_by(models.ChatMessage.timestamp.asc()).all()
    
    history = []
    for msg in db_messages:
        if msg.role == "human": history.append(HumanMessage(content=msg.content))
        elif msg.role == "ai": history.append(AIMessage(content=msg.content))
    
    history.append(HumanMessage(content=user_prompt))
    return history


# In Backend/services/chat_service.py

# ... (make sure all necessary imports are present)
from langgraph_core.utils.text_processing import preprocess_user_input
import re

def process_user_message_stream(db_session: Session, chat_session: models.ChatSession, user_prompt: str):
    """
    This is the definitive, stateful, hybrid router and streamer.
    It correctly implements the supervisor logic.
    """
    print("--- HYBRID STREAMING SERVICE ---")

    # 1. Reconstruct history and state
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

    # --- 2. IMPLEMENT HYBRID SUPERVISOR LOGIC ---
    
    # RULE 1: Python Safety Net for Resume Follow-ups
    if resume_text:
        user_input_lower = user_prompt.lower() # <-- BUG FIX #1
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
        
        # Use your full, detailed supervisor prompt here
        supervisor_prompt_template = ChatPromptTemplate.from_messages(...) # Paste your full prompt
        supervisor_chain = supervisor_prompt_template | supervisor_llm | StrOutputParser()
        
        route = supervisor_chain.invoke({
            "request": user_prompt, "history": history_str, "resume_exists": resume_exists
        }).strip().replace("`", "")
        print(f"--- SERVICE ROUTER: LLM decided route: {route} ---")

        # 3. SELECT THE CORRECT AGENT CHAIN AND PREPARE INPUTS
        if "CareerAdvisor" in route:
            agent_chain = create_career_advisor_chain()
            input_data = {"question": user_prompt, "resume_context": resume_text}
        elif "JobSearch" in route: # <-- BUG FIX #3
            parsed_args = llm_parser.invoke(user_prompt)
            agent_chain = create_job_search_chain()
            input_data = {"skills": parsed_args.skills, "location": parsed_args.location}
        elif "LearningPath" in route: # <-- BUG FIX #3
            # You would implement your robust JSON parsing here
            agent_chain = create_learning_path_chain()
            input_data = {"current_skills": "Not specified", "goal_role": user_prompt} # Simplified
        elif "ResumeQAAgent" in route:
            agent_chain = create_resume_qa_chain()
            input_data = {"resume_context": resume_text, "question": user_prompt}
        elif "END" in route: # <-- BUG FIX #2
            yield "Thank you! Have a great day."
            return # Exit the function cleanly
        else: # Default/Fallback
            print(f"--- ROUTER WARNING: Unknown route '{route}'. Defaulting to CareerAdvisor. ---")
            agent_chain = create_career_advisor_chain()
            input_data = {"question": user_prompt, "resume_context": resume_text}

    # --- 4. STREAM FROM THE CHOSEN AGENT AND SAVE TO DB ---
    full_ai_response = ""
    for token in agent_chain.stream(input_data):
        full_ai_response += token
        yield token

    # 5. Save the final conversation turn to the database
    db_user_message = models.ChatMessage(session_id=chat_session.id, role="human", content=user_prompt)
    db_ai_message = models.ChatMessage(session_id=chat_session.id, role="ai", content=full_ai_response)
    db_session.add_all([db_user_message, db_ai_message])
    db_session.commit()
    
def process_user_message(db_session: Session, chat_session: models.ChatSession, user_prompt: str) -> str:
    # This now simply collects the streamed response
    full_response = ""
    for token in process_user_message_stream(db_session, chat_session, user_prompt):
        full_response += token
    return full_response

def process_resume_file(chat_session_id: int, file_bytes: bytes, filename: str):
    """
    Analyzes a resume and saves it. Runs in a background thread.
    Creates its OWN thread-safe database session.
    """
    db: Session = SessionLocal() # Create a new session for this thread
    try:
        chat_session = db.query(models.ChatSession).filter(models.ChatSession.id == chat_session_id).first()
        if not chat_session:
            return

        resume_analyzer_agent = create_resume_analyzer_chain()
        
        # Pass the bytes and filename to the parser
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