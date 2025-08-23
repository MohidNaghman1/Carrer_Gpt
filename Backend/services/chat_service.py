from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage
from io import BytesIO
import json

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


def process_user_message_stream(db_session: Session, chat_session: models.ChatSession, user_prompt: str):
    """
    Manually routes to the correct agent and streams its response token-by-token.
    """
    print(f"--- Streaming message for session_id: {chat_session.id} ---")
    
    history = get_history(db_session, chat_session, user_prompt)
    
    # 1. Manually run the supervisor to decide the route
    route = supervisor_chain.invoke({"request": user_prompt}).strip().replace("`", "")
    print(f"--- Supervisor decided route: {route} ---")

    # 2. Select and stream from the appropriate agent's chain
    agent_chain = None
    input_data = {}

    if "CareerAdvisor" in route:
        agent_chain = create_career_advisor_chain()
        input_data = {"question": user_prompt}
    elif "JobSearch" in route:
        # Here we manually parse arguments for the job search agent
        parsed_args = llm_parser.invoke(user_prompt)
        agent_chain = create_job_search_chain()
        input_data = {"skills": parsed_args.skills, "location": parsed_args.location}
    elif "LearningPath" in route:
        # Similarly, you would parse args for learning path here if needed
        agent_chain = create_learning_path_chain()
        input_data = {"current_skills": "unknown", "goal_role": user_prompt} # Simplified for now
    elif "ResumeQAAgent" in route and chat_session.resume_text:
        agent_chain = create_resume_qa_chain()
        input_data = {"resume_context": chat_session.resume_text, "question": user_prompt}
    else: # Default fallback
        agent_chain = create_career_advisor_chain()
        input_data = {"question": user_prompt}

    # 3. Stream from the selected chain and save the full response
    full_ai_response = ""
    print(f"--- Streaming from agent: {route} ---")
    for token in agent_chain.stream(input_data):
        full_ai_response += token
        yield token

    # 4. After the stream is complete, save the conversation to the database
    print("--- Stream complete. Saving to DB. ---")
    db_user_message = models.ChatMessage(session_id=chat_session.id, role="human", content=user_prompt)
    db_ai_message = models.ChatMessage(session_id=chat_session.id, role="ai", content=full_ai_response)
    db_session.add_all([db_user_message, db_ai_message])
    db_session.commit()
    print("--- Saved streamed conversation to DB. ---")

# The NON-streaming function for the first message and resume analysis
def process_user_message(db_session: Session, chat_session: models.ChatSession, user_prompt: str) -> str:
    # This now simply collects the streamed response
    full_response = ""
    for token in process_user_message_stream(db_session, chat_session, user_prompt):
        full_response += token
    return full_response

def process_resume_file(db_session: Session, chat_session: models.ChatSession, file_bytes: bytes) -> str:
    """
    Analyzes a resume file, saves the text and analysis to the DB.
    """
    print(f"--- Processing resume for session_id: {chat_session.id} ---")

    # --- THIS IS THE NEW PART ---
    # Create an instance of the resume analyzer agent/chain
    resume_analyzer_agent = create_resume_analyzer_chain()
    # ---------------------------

    file_like_object = BytesIO(file_bytes)
    file_like_object.name = "resume.pdf"

    resume_text = extract_text_from_file(file_like_object)

    if "Error:" in resume_text:
        return resume_text

    # Now you can call invoke on the instance you just created
    analysis_string = resume_analyzer_agent.invoke({"resume_text": resume_text})

    # Save the extracted text to the session for future Q&A
    chat_session.resume_text = resume_text
    
    # Save the analysis as an AI message in the chat history
    db_human_message = models.ChatMessage(
        session_id=chat_session.id, role="human", content=f"Please analyze my uploaded resume: {file_like_object.name}"
    )
    db_ai_message = models.ChatMessage(
        session_id=chat_session.id, role="ai", content=analysis_string
    )
    # The session is already in the db_session from the endpoint, so we just need to add the messages
    db_session.add_all([db_human_message, db_ai_message])
    db_session.commit()

    return analysis_string