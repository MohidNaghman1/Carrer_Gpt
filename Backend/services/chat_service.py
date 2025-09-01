import json
import re
import traceback
from io import BytesIO
from typing import Generator, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic.v1 import Field, BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

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
            # Refresh the chat session to ensure it's still valid
            db_session.refresh(chat_session)
            
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
            # Don't re-raise the error to avoid breaking the stream
        
    except Exception as e:
        print(f"--- STREAMING ERROR: {e} ---")
        traceback.print_exc()
        yield f"I apologize, but I encountered an error: {str(e)}. Please try again."


def _execute_agent_node(agent_name: str, user_prompt: str, resume_text: Optional[str]) -> str:
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
                print(f"--- JOB SEARCH PARSED: skills='{skills}', location='{location}' ---")
            except Exception as parse_error:
                print(f"--- JOB SEARCH PARSE ERROR: {parse_error} ---")
                skills = "Not specified"
                location = "Not specified"
            
            agent_chain = create_job_search_chain()
            print(f"--- JOB SEARCH INPUT: skills='{skills}', location='{location}' ---")
            result = agent_chain.invoke({
                "skills": skills,
                "location": location
            })
            print(f"--- JOB SEARCH RAW RESULT: {result} ---")
            
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
            try:
                agent_chain = create_career_advisor_chain()
                print(f"--- CAREER ADVISOR INPUT: question='{user_prompt}', resume_context='{resume_text if resume_text else 'No resume provided'}' ---")
                result = agent_chain.invoke({
                    "question": user_prompt,
                    "resume_context": resume_text if resume_text else "No resume provided"
                })
                print(f"--- CAREER ADVISOR RAW RESULT: {result} ---")
            except Exception as chain_error:
                print(f"--- CAREER ADVISOR CHAIN ERROR: {chain_error} ---")
                result = "I'm having trouble providing career advice right now. Please try again in a moment."
        
        # Return the result directly (it's already a string)
        print(f"--- AGENT RESULT TYPE: {type(result)} ---")
        print(f"--- AGENT RESULT LENGTH: {len(str(result)) if result else 0} ---")
        print(f"--- AGENT RESULT PREVIEW: {str(result)[:100] if result else 'None'} ---")
        print(f"--- AGENT RESULT STRIPPED: {str(result).strip() if result else 'None'} ---")
        
        if result and str(result).strip():
            final_result = str(result).strip()
            print(f"--- RETURNING RESULT: {len(final_result)} characters ---")
            return final_result
        else:
            print("--- AGENT RETURNED EMPTY RESULT ---")
            return "I apologize, but I couldn't generate a response. Please try again."
            
    except Exception as e:
        print(f"--- AGENT EXECUTION ERROR for {agent_name}: {e} ---")
        traceback.print_exc()
        
        # Fallback response with more specific error information
        if agent_name == "ResumeQAAgent":
            return "I'm having trouble accessing your resume information. Please try again or re-upload your resume."
        elif agent_name == "LearningPath":
            return "I'm having trouble creating a learning path. Please try rephrasing your request with your current skills and desired role."
        elif agent_name == "JobSearch":
            return "I'm having trouble searching for jobs. Please try specifying the job title and location more clearly."
        elif agent_name == "ResumeAnalyst":
            return "I'm having trouble analyzing your resume. Please try uploading your resume again."
        elif agent_name == "CareerAdvisor":
            return "I'm having trouble providing career advice. Please try rephrasing your question."
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
        
        # Extract text from file - we need to determine file type from content
        # Try different file types since we don't have the original filename
        resume_text = None
        
        # Try PDF first
        try:
            resume_text = extract_text_from_file(file_content, "resume.pdf")
            if not resume_text.startswith("Error:"):
                print("--- SUCCESSFULLY EXTRACTED PDF ---")
            else:
                resume_text = None
        except:
            resume_text = None
        
        # Try DOCX if PDF failed
        if not resume_text or resume_text.startswith("Error:"):
            try:
                resume_text = extract_text_from_file(file_content, "resume.docx")
                if not resume_text.startswith("Error:"):
                    print("--- SUCCESSFULLY EXTRACTED DOCX ---")
                else:
                    resume_text = None
            except:
                resume_text = None
        
        # If both failed, return error
        if not resume_text or resume_text.startswith("Error:"):
            resume_text = "Error: Could not extract text from the uploaded file. Please ensure it's a valid PDF or DOCX file."
        
        if "Error:" in resume_text:
            print(f"--- RESUME EXTRACTION ERROR: {resume_text} ---")
            analysis_string = resume_text
        else:
            print("--- RESUME EXTRACTION SUCCESS ---")
            try:
                # Use the imported resume analyzer chain
                resume_analyzer_chain = create_resume_analyzer_chain()
                analysis_string = resume_analyzer_chain.invoke({"resume_text": resume_text})
                print(f"--- RESUME ANALYSIS COMPLETE: {len(analysis_string)} characters ---")
            except Exception as chain_error:
                print(f"--- RESUME ANALYZER CHAIN ERROR: {chain_error} ---")
                analysis_string = f"Error: Could not analyze the resume. Please try again. Details: {str(chain_error)}"
        
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
        try:
            db_session.add_all([human_message, ai_message])
            db_session.commit()
            print("--- RESUME MESSAGES SAVED TO DATABASE ---")
        except Exception as db_error:
            print(f"--- DATABASE SAVE ERROR: {db_error} ---")
            db_session.rollback()
            # Continue without failing the entire operation
        
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