import json
import re
import traceback
from io import BytesIO
from typing import Generator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic.v1 import Field, BaseModel
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from db import models
from db.database import SessionLocal
from langgraph_core.utils.file_parser import extract_text_from_file
from langgraph_core.graph_backend import supervisor_node
from langgraph_core.agents.chains import (
    create_career_advisor_chain,
    create_job_search_chain,
    create_learning_path_chain,
    create_resume_analyzer_chain,
    create_resume_qa_chain
)

# --- SYSTEM ARCHITECTURE OVERVIEW ---
# This service handles all chat interactions with intelligent agent routing
# 1. Uses supervisor_node from graph_backend.py for intelligent routing
# 2. Executes appropriate agent chains based on routing decision
# 3. Streams responses character by character for real-time display
# 4. Manages database operations for chat history and resume storage
# 5. Handles file uploads and resume analysis
# ---


def process_user_message_stream(db_session: Session, chat_session: models.ChatSession, user_prompt: str) -> Generator[str, None, None]:
    """
    Main streaming function that routes user messages and streams AI responses.
    Uses the supervisor_node from graph_backend.py for intelligent routing.
    """
    try:
        print(f"--- PROCESSING USER MESSAGE: {user_prompt[:50]}... ---")
        
        # Get resume text from chat session
        resume_text = chat_session.resume_text
        
        # Create agent state for supervisor
        agent_state = {
            "messages": [HumanMessage(content=user_prompt)],
            "resume_text": resume_text,
            "file_data": None
        }
        
        # Use supervisor to determine next agent
        print("--- CONSULTING SUPERVISOR ---")
        supervisor_result = supervisor_node(agent_state)
        next_agent = supervisor_result.get("next", "CareerAdvisor")
        print(f"--- SUPERVISOR DECISION: {next_agent} ---")
        
        # Execute the chosen agent and stream response
        print(f"--- EXECUTING AGENT: {next_agent} ---")
        agent_response = _execute_agent_node(next_agent, user_prompt, resume_text)
        
        # Stream the response character by character
        print("--- STARTING STREAM ---")
        for char in agent_response:
            yield char
        
        print("--- STREAM COMPLETE ---")
        
        # Save messages to database after streaming is complete
        print("--- SAVING MESSAGES TO DATABASE ---")
        try:
            # Create and save user message
            user_message = models.ChatMessage(
                session_id=chat_session.id,
                role="human",
                content=user_prompt
            )
            
            # Create and save AI message
            ai_message = models.ChatMessage(
                session_id=chat_session.id,
                role="ai",
                content=agent_response
            )
            
            # Add messages to database
            db_session.add_all([user_message, ai_message])
            db_session.commit()
            print("--- MESSAGES SAVED TO DATABASE ---")
            
        except Exception as db_error:
            print(f"--- DATABASE SAVE ERROR: {db_error} ---")
            db_session.rollback()
        
    except Exception as e:
        print(f"--- STREAMING ERROR: {e} ---")
        traceback.print_exc()
        yield f"I apologize, but I encountered an error: {str(e)}. Please try again."


def _execute_agent_node(agent_name: str, user_prompt: str, resume_text: str) -> str:
    """
    Execute the appropriate agent node and return the response.
    Uses the imported chain creation functions for direct execution.
    """
    try:
        # Route to appropriate agent chain
        if agent_name == "ResumeQAAgent":
            print("--- EXECUTING: ResumeQAAgent ---")
            agent_chain = create_resume_qa_chain()
            result = agent_chain.invoke({
                "resume_context": resume_text if resume_text else "No resume provided",
                "question": user_prompt
            })
            
        elif agent_name == "LearningPath":
            print("--- EXECUTING: LearningPath ---")

            
            llm_parser = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
            parser_prompt = ChatPromptTemplate.from_template(
                """You are a highly efficient text-to-JSON converter. Your ONLY job is to extract information from the user's request and format it as a single, valid JSON object.
                You MUST respond with ONLY the JSON object and nothing else. Do not add any conversational text, introductions, or Markdown formatting.

                The JSON schema you must adhere to is:
                {{"current_skills": "a comma-separated list of skills", "goal_role": "the user's desired job role"}}

                - If no skills are mentioned, use "Not specified" for the current_skills value.
                - If no goal role is mentioned, use "Not specified" for the goal_role value.

                User Request: "{request}"

                Your JSON Response:
                """
            )
            
            parser_chain = parser_prompt | llm_parser | StrOutputParser()
            
            try:
                raw_response = parser_chain.invoke({"request": user_prompt})
                match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if match:
                    json_string = match.group(0)
                    parsed_args = json.loads(json_string)
                    current_skills = parsed_args.get("current_skills", "Not specified")
                    goal_role = parsed_args.get("goal_role", "Not specified")
                else:
                    current_skills = "Not specified"
                    goal_role = "Not specified"
            except:
                current_skills = "Not specified"
                goal_role = "Not specified"
            
            agent_chain = create_learning_path_chain()
            result = agent_chain.invoke({
                "current_skills": current_skills,
                "goal_role": goal_role
            })
            
        elif agent_name == "JobSearch":
            print("--- EXECUTING: JobSearch ---")
            # Use LLM parser to extract skills and location from user query

            
            class JobSearchParams(BaseModel):
                skills: str = Field(description="The job title or primary skills the user is looking for.")
                location: str = Field(description="The geographic location the user wants to search in. Default to 'Not specified' if none is mentioned.")
            
            llm_parser = ChatGroq(model="llama-3.1-8b-instant", temperature=0).with_structured_output(JobSearchParams)
            
            parser_prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a data extraction specialist. Your only job is to analyze the user's request and extract the 'skills' (job title) and 'location' into a JSON object that matches the `JobSearchParams` schema. Follow the examples precisely.\n\n"
                 "--- EXAMPLES ---\n"
                 "User Request: 'find me AI Engineer jobs in Pakistan'\n"
                 "Your JSON Response: {{\"skills\": \"AI Engineer\", \"location\": \"Pakistan\"}}\n\n"
                 "User Request: 'remote software developer positions'\n"
                 "Your JSON Response: {{\"skills\": \"software developer\", \"location\": \"Remote\"}}\n\n"
                 "User Request: 'what are some data science jobs?'\n"
                 "Your JSON Response: {{\"skills\": \"data science\", \"location\": \"Not specified\"}}\n"
                 "--- END EXAMPLES ---"
                ),
                ("user", "User Request: \"{request}\"")
            ])
            
            try:
                parsed_params = (parser_prompt | llm_parser).invoke({"request": user_prompt})
                skills = parsed_params.skills
                location = parsed_params.location
            except:
                skills = "Not specified"
                location = "Not specified"
            
            agent_chain = create_job_search_chain()
            result = agent_chain.invoke({
                "skills": skills,
                "location": location
            })
            
        elif agent_name == "ResumeAnalyst":
            print("--- EXECUTING: ResumeAnalyst ---")
            agent_chain = create_resume_analyzer_chain()
            result = agent_chain.invoke({
                "resume_text": resume_text if resume_text else "No resume provided"
            })
            
        elif agent_name == "ResumeQAAgent":
            print("--- EXECUTING: ResumeQAAgent ---")
            agent_chain = create_resume_qa_chain()
            result = agent_chain.invoke({
                "resume_context": resume_text if resume_text else "No resume provided",
                "question": user_prompt
            })
            
        else:
            # Default to CareerAdvisor
            print("--- EXECUTING: CareerAdvisor ---")
            agent_chain = create_career_advisor_chain()
            result = agent_chain.invoke({
                "question": user_prompt,
                "resume_context": resume_text if resume_text else "No resume provided"
            })
        
        # Return the result directly (it's already a string)
        print(f"--- AGENT RESULT TYPE: {type(result)} ---")
        print(f"--- AGENT RESULT LENGTH: {len(str(result)) if result else 0} ---")
        
        if result:
            return str(result)
        else:
            print("--- AGENT RETURNED EMPTY RESULT ---")
            return "I apologize, but I couldn't generate a response. Please try again."
            
    except Exception as e:
        print(f"--- AGENT EXECUTION ERROR for {agent_name}: {e} ---")
        traceback.print_exc()
        
        # Fallback response
        if agent_name == "ResumeQAAgent":
            return "I'm having trouble accessing your resume information. Please try again or re-upload your resume."
        elif agent_name == "LearningPath":
            return "I'm having trouble creating a learning path. Please try rephrasing your request with your current skills and desired role."
        elif agent_name == "JobSearch":
            return "I'm having trouble searching for jobs. Please try specifying the job title and location more clearly."
        elif agent_name == "ResumeAnalyst":
            return "I'm having trouble analyzing your resume. Please try uploading your resume again."
        else:
            return "I'm having trouble processing your request. Please try again or rephrase your question."


def process_user_message(db_session: Session, chat_session: models.ChatSession, user_prompt: str) -> str:
    """
    Non-streaming version for compatibility.
    """
    full_response = ""
    for token in process_user_message_stream(db_session, chat_session, user_prompt):
        full_response += token
    return full_response


def process_resume_file(db_session: Session, chat_session_id: int, file_content: bytes) -> str:
    """
    Process uploaded resume file and return analysis.
    """
    try:
        print(f"--- PROCESSING RESUME FILE ---")
        
        # Get chat session
        chat_session = db_session.query(models.ChatSession).filter(
            models.ChatSession.id == chat_session_id
        ).first()
        
        if not chat_session:
            return "Error: Chat session not found."
        
        # Extract text from file
        resume_text = extract_text_from_file(file_content, "resume.pdf")
        
        if "Error:" in resume_text:
            print(f"--- RESUME EXTRACTION ERROR: {resume_text} ---")
            analysis_string = resume_text
        else:
            print("--- RESUME EXTRACTION SUCCESS ---")
            # Use the imported resume analyzer chain
            resume_analyzer_chain = create_resume_analyzer_chain()
            analysis_string = resume_analyzer_chain.invoke({"resume_text": resume_text})
        
        # Update chat session with resume text
        chat_session.resume_text = resume_text
        
        # Create messages for the database
        human_message = models.ChatMessage(
            session_id=chat_session_id,
            role="human",
            content="Uploaded resume for analysis"
        )
        
        ai_message = models.ChatMessage(
            session_id=chat_session_id,
            role="ai",
            content=analysis_string
        )
        
        # Add messages to database
        db_session.add_all([human_message, ai_message])
        db_session.commit()
        
        print("--- RESUME PROCESSING COMPLETE ---")
        return analysis_string
        
    except Exception as e:
        print(f"--- RESUME PROCESSING ERROR: {e} ---")
        traceback.print_exc()
        return f"Error processing resume: {str(e)}"


def get_chat_history(db_session: Session, session_id: int) -> list[models.ChatMessage]:
    """
    Get chat history for a session.
    """
    try:
        messages = db_session.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id
        ).order_by(models.ChatMessage.timestamp.asc()).all()
        
        return messages
        
    except Exception as e:
        print(f"--- CHAT HISTORY ERROR: {e} ---")
        traceback.print_exc()
        return []


def create_chat_session(db_session: Session, user_id: int, title: str = None, first_message: str = None) -> models.ChatSession:
    """
    Create a new chat session.
    """
    try:
        # Generate title from first message if not provided
        if not title and first_message:
            words = first_message.split()[:4]
            title = " ".join(words) + "..." if len(first_message.split()) > 4 else first_message
        
        # Create new chat session
        new_session = models.ChatSession(
            user_id=user_id,
            title=title or "New Chat Session"
        )
        
        db_session.add(new_session)
        db_session.commit()
        db_session.refresh(new_session)
        
        print(f"--- CREATED CHAT SESSION: {new_session.id} ---")
        return new_session
        
    except Exception as e:
        print(f"--- CREATE SESSION ERROR: {e} ---")
        traceback.print_exc()
        db_session.rollback()
        raise


def update_chat_session_title(db_session: Session, session_id: int, new_title: str):
    """
    Update chat session title.
    """
    try:
        chat_session = db_session.query(models.ChatSession).filter(
            models.ChatSession.id == session_id
        ).first()
        
        if chat_session:
            chat_session.title = new_title
            db_session.commit()
            print(f"--- UPDATED SESSION TITLE: {new_title} ---")
        
    except Exception as e:
        print(f"--- UPDATE TITLE ERROR: {e} ---")
        traceback.print_exc()
        db_session.rollback()