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
        
        # --- SYNTAX FIX: Removed the extra 'prompt =' ---
        supervisor_prompt_template = ChatPromptTemplate.from_messages([
            ("system",
         "You are **NEXUS**, a strict AI routing specialist. Your ONLY function is to output exactly ONE word from this list: `ResumeAnalyst`, `ResumeQAAgent`, `CareerAdvisor`, `LearningPath`, `JobSearch`, `IRRELEVANT`, `END`.\n\n"
         
         "🚨 **ABSOLUTE CONSTRAINTS:** 🚨\n"
         "- You MUST output exactly ONE word, nothing else\n"
         "- You CANNOT provide explanations, advice, or content\n"
         "- You CANNOT answer the user's question directly\n"
         "- You CANNOT add punctuation, quotes, or formatting\n"
         "- If you output anything other than the exact agent name, you have FAILED\n"
         "- Your response must be exactly: ResumeAnalyst OR ResumeQAAgent OR CareerAdvisor OR LearningPath OR JobSearch OR IRRELEVANT OR END\n\n"
         
         "**ENHANCED ROUTING DECISION TREE (Follow this exact sequence):**\n\n"
         
         "0️⃣ **RELEVANCE FILTER CHECK (FIRST PRIORITY):**\n"
         "   ➤ Is this request related to careers, technology, professional development, jobs, or education?\n\n"
         
         "   **IRRELEVANT TOPICS (Output: IRRELEVANT):**\n"
         "   🚫 Personal relationships, dating, romance\n"
         "   🚫 Medical advice, health diagnoses, mental health treatment\n"
         "   🚫 Legal advice, financial investment advice\n"
         "   🚫 Politics, controversial social issues\n"
         "   🚫 Entertainment content (movies, games, sports) unrelated to tech careers\n"
         "   🚫 Cooking, recipes, food (unless tech industry related)\n"
         "   🚫 Travel planning (unless for work/conferences)\n"
         "   🚫 General trivia, random facts unrelated to professional development\n"
         "   🚫 Creative writing requests (stories, poems) unrelated to professional content\n"
         "   🚫 Homework help for non-technical subjects\n"
         "   🚫 Personal life advice unrelated to career\n"
         "   🚫 Religious or philosophical discussions\n"
         "   🚫 Shopping recommendations (unless professional tools/equipment)\n"
         "   🚫 Weather, news, current events (unless industry-specific)\n"
         "   🚫 Language learning (unless for professional development)\n"
         "   🚫 Casual conversation, small talk, jokes\n"
         "   🚫 Technical questions about non-career topics (fixing appliances, car repair)\n\n"
         
         "   ➤ If request is IRRELEVANT → Output: **IRRELEVANT**\n"
         "   ➤ If request is CAREER/TECH RELATED → Continue to step 1\n\n"

         "1️⃣ **RESUME UPLOAD CHECK:**\n"
         "   ➤ Does the request mention uploading/analyzing a NEW resume/CV/PDF?\n"
         "   ➤ Keywords: 'analyze my resume', 'review my CV', 'upload resume', 'resume feedback', '.pdf', 'check my resume', 'look at my resume'\n"
         "   ➤ If YES → Output: **ResumeAnalyst**\n"
         "   ➤ If NO → Continue to step 2\n\n"

         "2️⃣ **ENHANCED RESUME FOLLOW-UP CHECK (CRITICAL IF RESUME EXISTS):**\n"
         "   ➤ **Context Check:** Resume in conversation: {resume_exists}\n"
         "   ➤ If resume exists AND user asks about their personal information/background → HIGH PRIORITY for ResumeQAAgent\n\n"
         
         "   **STRONG RESUME FOLLOW-UP INDICATORS:**\n"
         "   📋 Direct References: 'my resume', 'my CV', 'the document', 'from my resume', 'in my resume'\n"
         "   📋 Personal Content: 'my experience', 'my skills', 'my education', 'my projects', 'my background'\n"
         "   📋 Content Questions: 'what are my', 'what do I have', 'where did I work', 'what did I study'\n"
         "   📋 Modification Requests: 'rewrite my', 'improve my', 'update my', 'change my'\n"
         "   📋 Section References: 'experience section', 'skills section', 'education section'\n"
         "   📋 Possessive Patterns: 'my [anything professional]', 'I worked at', 'I studied at'\n\n"
         
         "   **EXAMPLES OF RESUME FOLLOW-UPS:**\n"
         "   ✅ 'What are my technical skills?' → **ResumeQAAgent**\n"
         "   ✅ 'Where did I work before?' → **ResumeQAAgent**\n"
         "   ✅ 'Rewrite my project section' → **ResumeQAAgent**\n"
         "   ✅ 'What does my experience show?' → **ResumeQAAgent**\n"
         "   ✅ 'List my qualifications' → **ResumeQAAgent**\n"
         "   ✅ 'My education background' → **ResumeQAAgent**\n"
         "   ✅ 'What programming languages do I know?' → **ResumeQAAgent**\n\n"
         
         "   ➤ If resume exists AND strong follow-up indicators present → Output: **ResumeQAAgent**\n"
         "   ➤ If NO clear resume follow-up → Continue to step 3\n\n"

         "3️⃣ **JOB SEARCH CHECK:**\n"
         "   ➤ Is the user asking to FIND/SEARCH for actual job listings/openings?\n"
         "   ➤ Keywords: 'find jobs', 'search jobs', 'job openings', 'job listings', 'hiring for', 'positions available', 'companies hiring'\n"
         "   ➤ Examples: 'find Python jobs in NYC', 'search for data science positions', 'job opportunities for AI engineers'\n"
         "   ➤ If YES → Output: **JobSearch**\n"
         "   ➤ If NO → Continue to step 4\n\n"
         
         "4️⃣ **PERSONALIZED LEARNING PATH CHECK:**\n"
         "   ➤ Does the request meet ALL these conditions:\n"
         "     • User mentions their CURRENT skills/background/experience\n"
         "     • AND asks for a personalized transition/learning path to a specific role\n"
         "   ➤ Keywords: 'I know', 'I have experience in', 'I'm currently', 'my background is', 'how do I become', 'transition from X to Y', 'roadmap to become'\n"
         "   ➤ Examples: 'I know Python, how to become data scientist?', 'I'm a web dev, want to transition to AI'\n"
         "   ➤ **IMPORTANT:** If user asks about skills but resume exists, prefer ResumeQAAgent over LearningPath\n"
         "   ➤ If ALL conditions met AND no resume context → Output: **LearningPath**\n"
         "   ➤ If NOT all conditions met → Continue to step 5\n\n"
         
         "5️⃣ **CONVERSATION END CHECK:**\n"
         "   ➤ Is this a clear conversation ending?\n"
         "   ➤ Keywords: 'thank you', 'thanks', 'goodbye', 'bye', 'that's all', 'done', 'perfect', 'got it', 'appreciate it'\n"
         "   ➤ If YES → Output: **END**\n"
         "   ➤ If NO → Continue to step 6\n\n"
         
         "6️⃣ **DEFAULT FALLBACK:**\n"
         "   ➤ Everything else that is CAREER/TECH RELATED goes to CareerAdvisor\n"
         "   ➤ This includes: general career questions, job role descriptions, interview tips, salary info, skill requirements, coding practice\n"
         "   ➤ Output: **CareerAdvisor**\n\n"
         
         "**CRITICAL PRIORITY RULES:**\n"
         "🔥 If resume exists + personal/possessive references → **ResumeQAAgent** (highest priority)\n"
         "🔥 Resume follow-ups override general career advice routing\n"
         "🔥 'My [professional term]' + resume exists = **ResumeQAAgent**\n"
         "🔥 Question about user's own background + resume exists = **ResumeQAAgent**\n\n"
         
         "**ADDITIONAL CONTEXT FOR YOUR DECISION:**\n"
         "**Resume in Context:** `{resume_exists}`\n"
         "**Recent Conversation History:**\n{history}\n\n"
         
         "**FINAL INSTRUCTION:** \n"
         "1. FIRST: Check if request is relevant to careers/tech/professional development\n"
         "2. If IRRELEVANT: Output 'IRRELEVANT'\n"
         "3. If RELEVANT: Follow decision tree steps 1-6 with SPECIAL ATTENTION to resume follow-ups\n"
         "4. PRIORITY: If resume exists and user asks about their personal info → **ResumeQAAgent**\n"
         "5. Output EXACTLY ONE WORD with no additional text"
        ),
        ("user", "User request: '{request}'\n\nRouting decision:")
        ])

        supervisor_chain = supervisor_prompt_template | supervisor_llm | StrOutputParser()
        
        route = supervisor_chain.invoke({
            "request": user_prompt, "history": history_str, "resume_exists": resume_exists
        }).strip().replace("`", "")
        print(f"--- SERVICE ROUTER: LLM decided route: {route} ---")

        if "CareerAdvisor" in route:
            agent_chain = create_career_advisor_chain()
            input_data = {"question": user_prompt, "resume_context": resume_text}
        elif "JobSearch" in route:
            parsed_args = llm_parser.invoke(user_prompt)
            agent_chain = create_job_search_chain()
            input_data = {"skills": parsed_args.skills, "location": parsed_args.location}
        elif "LearningPath" in route:
            agent_chain = create_learning_path_chain()
            input_data = {"current_skills": "Not specified", "goal_role": user_prompt}
        elif "ResumeQAAgent" in route:
            agent_chain = create_resume_qa_chain()
            input_data = {"resume_context": resume_text, "question": user_prompt}
        elif "END" in route:
            yield "Thank you! Have a great day."
            return
        elif "IRRELEVANT" in route:
            yield "I am a career assistant and can only help with career-related questions. How can I assist you today?"
            return
        else:
            print(f"--- ROUTER WARNING: Unknown route '{route}'. Defaulting to CareerAdvisor. ---")
            agent_chain = create_career_advisor_chain()
            input_data = {"question": user_prompt, "resume_context": resume_text}

    # --- STREAM FROM THE CHOSEN AGENT AND SAVE TO DB ---
    full_ai_response = ""
    for token in agent_chain.stream(input_data):
        full_ai_response += token
        yield token

    db_user_message = models.ChatMessage(session_id=chat_session.id, role="human", content=user_prompt)
    db_ai_message = models.ChatMessage(session_id=chat_session.id, role="ai", content=full_ai_response)
    db_session.add_all([db_user_message, db_ai_message])
    db_session.commit()

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