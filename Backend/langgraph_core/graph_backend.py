import os,json,re
import operator
from io import BytesIO
from typing import TypedDict, Annotated, Sequence,Any,Literal,Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from pydantic.v1 import Field,BaseModel
from langgraph_core.agents.chains import create_resume_analyzer_chain, create_resume_qa_chain, create_career_advisor_chain, create_learning_path_chain, create_job_search_chain
from langgraph_core.utils.file_parser import extract_text_from_file
from langgraph_core.utils.text_processing import preprocess_user_input

# --- 1. State definition is correct ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    resume_text: str | None
    file_data: bytes | None

class SupervisorDecision(BaseModel):
    next_agent: Literal["ResumeAnalyst", "CareerAdvisor", "LearningPath", "JobSearch", "END"] = Field(...) # <= ADD "JobSearch"
    args: Dict[str, Any] = Field(...)

class JobSearchParams(BaseModel):
    """The parameters required for the Job Search agent."""
    skills: str = Field(description="The job title or primary skills the user is looking for.")
    location: str = Field(description="The geographic location the user wants to search in. Default to 'Not specified' if none is mentioned.")


llm_parser = ChatGroq(model="llama3-70b-8192", temperature=0).with_structured_output(JobSearchParams)

# --- 2. Initialization is correct ---
resume_analyzer_agent = create_resume_analyzer_chain()
career_advisor_agent = create_career_advisor_chain()
learning_path_agent = create_learning_path_chain()
job_search_agent = create_job_search_chain()
resume_qa_agent = create_resume_qa_chain()

supervisor_llm = ChatGroq(model="llama3-70b-8192", temperature=0)


# --- 3. Node Definitions ---


# --- THIS IS THE NEW, SMARTER SUPERVISOR NODE ---
def supervisor_node(state: AgentState) -> dict:
    """
    This is the definitive hybrid supervisor. It uses a Python rule to prevent loops
    and a powerful, rule-based LLM prompt for intelligent routing with strict role identification.
    """
    print("---SUPERVISOR (HYBRID + INTELLIGENT ROUTING)---")
    
    # --- RULE 1: PYTHON-BASED SAFETY NET (Unbreakable Loop Prevention) ---
    # This is our ironclad guarantee against infinite loops.
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage):
        print("Supervisor Safety Net: Last message was from an agent. Ending turn.")
        return {"next": "END"}
    
    if state.get("resume_text"):
        user_input_lower = last_message.content.lower()
        # Keywords that strongly suggest a follow-up question.
        follow_up_keywords = ["resume", "cv", "my document", "project", "experience", "skill", "rewrite"]
        if any(keyword in user_input_lower for keyword in follow_up_keywords):
            print("---HYBRID SUPERVISOR: Detected resume follow-up. Routing to ResumeQAAgent.---")
            return {"next": "ResumeQAAgent"}
    
    # --- RULE 2: LLM-POWERED ROUTING (With strict role identification) ---
    # If the last message was from the user, the LLM will decide the next step.
    prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are **NEXUS**, an elite AI routing specialist for a comprehensive career guidance system. Your ONLY job is to analyze the user's message and output exactly ONE word from this list: `ResumeAnalyst`, `CareerAdvisor`, `LearningPath`, `JobSearch`, `END`.\n\n"
     
     "**CRITICAL INSTRUCTIONS:**\n"
     "- Read the user's request carefully and identify the PRIMARY intent\n"
     "- Match it to the most appropriate specialist agent based on the rules below\n"
     "- Output ONLY the agent name, nothing else\n"
     "- Do not explain your reasoning or add punctuation\n"
     "- When in doubt between two agents, follow the priority order in the decision process\n\n"
     
     "**STRICT ROUTING RULES:**\n\n"
        
    "🔍 **ResumeAnalyst** - Route here for the **initial request** to analyze a resume:\n"
    " ✅ Mentions 'resume', 'CV', '.pdf', '.docx', 'review my resume'.\n"
    " 🎯 **Priority:** Highest - Always route here for the FIRST resume request.\n\n"

    "🗣️ **ResumeQAAgent** - Route here for **follow-up questions** about a resume that has *already been analyzed*:\n"
    "   ✅ Assumes a resume is already in context.\n"
    "   ✅ Asks specific questions: 'what did my resume say about X?', 'rewrite my project description', 'tell me more about the feedback on my skills section'.\n"
    "   🎯 **Priority:** Second highest. If the conversation is about a resume, use this agent.\n\n"

     "🔎 **JobSearch** - Route here if user wants to find actual job opportunities:\n"
     "   ✅ Job hunting keywords: 'find jobs', 'search for jobs', 'job openings', 'job listings'\n"
     "   ✅ Active job seeking: 'jobs for [role]', 'hiring for [position]', 'job opportunities in [location]'\n"
     "   ✅ Specific searches: 'Python jobs in NYC', 'remote data scientist positions', 'AI engineer openings'\n"
     "   ✅ Examples: 'Find me data science jobs', 'Search for ML engineer positions in California', 'Job openings for Python developers'\n"
     "   ❌ Counter-examples: 'What does a data scientist do?' (that's CareerAdvisor), 'How to become an AI engineer?' (that's CareerAdvisor or LearningPath)\n"
     "   🎯 **Priority:** Second highest - Route here for active job searching requests\n\n"
     
     "📚 **LearningPath** - Route here ONLY if ALL conditions are met:\n"
     "   ✅ User mentions their CURRENT skills/background explicitly (e.g., 'I know Python', 'I have experience in X', 'I'm currently a Y')\n"
     "   ✅ AND asks for personalized transition/learning path to a specific target role\n"
     "   ✅ Transition keywords: 'how do I become', 'transition to', 'switch careers to', 'move from X to Y'\n"
     "   ✅ Examples: 'I know Python, how do I become a Data Scientist?', 'I'm a web developer, how to transition to ML?', 'I have Java experience, want to become an AI engineer'\n"
     "   ❌ Counter-examples: 'What is a data scientist roadmap?' (no current skills mentioned → CareerAdvisor)\n"
     "   🎯 **Priority:** Third - Route here only for personalized career transitions\n\n"
     
     "💼 **CareerAdvisor** - This is the DEFAULT. Route here for:\n"
     "   ✅ General career questions without mentioning current skills\n"
     "   ✅ Job role descriptions: 'what is a data scientist?', 'what does an AI engineer do?', 'roles in tech'\n"
     "   ✅ General roadmaps: 'roadmap for becoming X', 'how to become Y' (without mentioning current skills)\n"
     "   ✅ Interview preparation: 'interview tips', 'how to prepare for tech interviews', 'common interview questions'\n"
     "   ✅ Salary and compensation: 'salary for data scientists', 'how much do AI engineers make?'\n"
     "   ✅ Skills and requirements: 'what skills needed for X role?', 'requirements for becoming Y'\n"
     "   ✅ Industry insights: 'job market for AI', 'career prospects in tech', 'trends in data science'\n"
     "   ✅ Career advice: 'how to negotiate salary', 'career growth tips', 'networking strategies'\n"
     "   ✅ Any career question that doesn't fit the other specific criteria\n"
     "   🎯 **Priority:** Default fallback for all general career guidance\n\n"
     
     "🚪 **END** - Route here ONLY if:\n"
     "   ✅ Clear conversation ending: 'thanks', 'thank you', 'goodbye', 'bye', 'that's all', 'done'\n"
     "   ✅ Satisfaction indicators: 'that helps', 'perfect', 'got it', 'no more questions'\n\n"
     
     "**DECISION PROCESS (Follow this exact order):**\n"
     "1. 🔍 Does it mention resume/CV/file for the FIRST time? → **ResumeAnalyst**\n"
     "2. 🗣️ Is it a follow-up question about an already analyzed resume? → **ResumeQAAgent**\n"
     "3. 🔎 Does it ask to find/search for actual job listings? → **JobSearch**\n"
     "4. 📚 Does it mention current skills AND ask for transition path? → **LearningPath**\n"
     "5. 🚪 Is it a clear goodbye/thanks? → **END**\n"
     "6. 💼 Everything else → **CareerAdvisor**\n\n"
     
     "**COMMON CONFUSION PATTERNS:**\n"
     "❗ 'Jobs for data scientists' → **JobSearch** (looking for listings)\n"
     "❗ 'What do data scientists do?' → **CareerAdvisor** (role information)\n"
     "❗ 'I know Python, want data science jobs' → **JobSearch** (current skills + job search)\n"
     "❗ 'I know Python, how to become data scientist?' → **LearningPath** (current skills + learning path)\n"
     "❗ 'Data scientist roadmap' → **CareerAdvisor** (general roadmap, no current skills)\n\n"
     
     "**FINAL REMINDER:** Output exactly one word with no quotes, periods, or explanations: ResumeAnalyst, CareerAdvisor, LearningPath, JobSearch, or END"
    ),
    ("user", "User request: '{request}'\n\nRouting decision:")
])
    original_input = last_message.content
    processed_input = preprocess_user_input(original_input)
    runnable = prompt | supervisor_llm | StrOutputParser()
    next_agent = runnable.invoke({"request": processed_input})
    
    cleaned_destination = next_agent.strip().replace("`", "").replace("'", "").replace('"', '')
    print(f"Supervisor LLM Decision: '{cleaned_destination}'")
    valid_destinations = ["ResumeAnalyst", "ResumeQAAgent", "CareerAdvisor", "LearningPath", "JobSearch", "END"]
    
    if cleaned_destination in valid_destinations:
        return {"next": cleaned_destination}
    else:
        print(f"---SUPERVISOR WARNING: LLM returned invalid destination '{cleaned_destination}'. Defaulting to CareerAdvisor.---")
        return {"next": "CareerAdvisor"}
    
# In Graph_backend.py

# --- REPLACE your old career_advisor_node with this new, robust version ---
def career_advisor_node(state: AgentState) -> dict:
    print("---AGENT: CareerAdvisor---")
    answer_string = ""
    try:
        question = state["messages"][-1].content
        # This is the line that might fail
        answer_string = career_advisor_agent.invoke({"question": question})
        
        # A check in case the agent returns an empty or error-like string
        if not answer_string or "error" in answer_string.lower():
            print(f"---CAREER ADVISOR: Agent returned an empty or error-like response: '{answer_string}'")
            raise ValueError("Agent returned a non-viable answer.")

    except Exception as e:
        # This is our safety net for this specific node
        print(f"---!!! CAREER ADVISOR NODE FAILED !!!---")
        print(f"---Error: {e}")
        # Provide a specific, helpful message to the user
        answer_string = (
            "I'm sorry, my Career Advisor module is currently experiencing an issue and I can't access my knowledge base. "
            "This could be due to a temporary connection problem. Please try a different question or check back in a moment."
        )
        
    return {"messages": [AIMessage(content=answer_string)], "next": "supervisor"}
    
def learning_path_node(state: AgentState) -> dict:
    """
    This agent uses a reliable LLM parser to intelligently extract arguments,
    then calls the main chain to generate the learning path.
    """
    print("---AGENT: LearningPath (with ROBUST Smart Parsing)---")
    user_input = state["messages"][-1].content
    
    # We use a simple, fast LLM for the parsing task.
    llm_parser = ChatGroq(model="llama3-8b-8192", temperature=0)

    # Step 1: A much stricter prompt to guide the LLM.
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
    
    path_string = ""
    try:
        # Step 2: Invoke the parser and get the raw string output.
        raw_response = parser_chain.invoke({"request": user_input})
        print(f"---LLM Parser Raw Output: '{raw_response}'---")

        # Step 3: This is the robust parsing logic. It finds the JSON within the string.
        # It looks for the first '{' and the last '}' to handle cases where the LLM adds extra text.
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if not match:
            raise ValueError("LLM did not produce a parsable JSON object.")
        
        json_string = match.group(0)
        parsed_args = json.loads(json_string) # Use Python's built-in JSON parser
        
        current_skills = parsed_args.get("current_skills", "Not specified")
        goal_role = parsed_args.get("goal_role", "Not specified")
        
        print(f"---LEARNING PATH PARSED PARAMS: Skills='{current_skills}', Goal='{goal_role}'---")

        # Step 4: Call the main agent chain with the correctly parsed arguments.
        if goal_role == "Not specified":
            path_string = "To generate a learning path, please tell me your desired job role so I can create a personalized plan for you."
        else:
            path_string = learning_path_agent.invoke({
                "current_skills": current_skills,
                "goal_role": goal_role
            })

    except Exception as e:
        # Step 5: This is our safety net.
        print(f"---LEARNING PATH PARSING FAILED: {e}---")
        path_string = "I'm sorry, I had trouble understanding your request for a learning path. Could you please clearly state your current skills (if any) and your goal role?"

    return {"messages": [AIMessage(content=path_string)], "next": "supervisor"}

def job_search_node(state: AgentState) -> dict:
    """
    This agent uses a powerful LLM parser with explicit examples to reliably extract
    the user's desired skills and location before calling the job search chain.
    """
    print("---AGENT: JobSearch (with Upgraded Smart Parsing)---")
    user_input = state["messages"][-1].content
    
    # --- THIS IS THE UPGRADED, BULLETPROOF PROMPT ---
    # It uses "few-shot" prompting (providing examples) to train the LLM on the fly.
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
    
    runnable = parser_prompt | llm_parser
    
    try:
        # Step 1: Invoke the parser to get structured data.
        parsed_params: JobSearchParams = runnable.invoke({"request": user_input})
        
        skills = parsed_params.skills
        location = parsed_params.location
        
        print(f"---JOB SEARCH PARSED PARAMS: Skills='{skills}', Location='{location}'---")

        # Step 2: A safety check. If the parser fails to find a location, ask the user.
        if location == "Not specified":
            job_postings_summary = "It looks like you're searching for a job. Could you please specify a location (e.g., 'India', 'Remote', 'London')?"
        else:
            # Step 3: Call the main agent chain with the correctly parsed arguments.
            job_postings_summary = job_search_agent.invoke({"skills": skills, "location": location})

    except Exception as e:
        # Step 4: This is our final safety net.
        print(f"---JOB SEARCH PARSING FAILED: {e}---")
        job_postings_summary = "I'm sorry, I had trouble understanding your request for a job search. Could you please clearly state the job title and location you're interested in?"

    return {"messages": [AIMessage(content=job_postings_summary)], "next": "supervisor"}
# In Graph_backend.py

# In Graph_backend.py

# In Graph_backend.py

# You may need to import BytesIO
from io import BytesIO

def resume_analyzer_node(state: AgentState) -> dict:
    print("---AGENT: ResumeAnalyst---")
    
    # --- THIS IS THE NEW LOGIC ---
    # 1. Get the file data directly from the state.
    file_bytes = state.get("file_data")

    if file_bytes:
        print("--- Found resume data in state. Processing... ---")
        
        # 2. Use BytesIO to treat the bytes as a file for PyMuPDF.
        #    We add a dummy name '.pdf' so the parser knows the file type.
        file_like_object = BytesIO(file_bytes)
        file_like_object.name = "resume.pdf" # Dummy name for filetype detection
        
        # 3. Call your existing file parser with the file-like object.
        resume_text = extract_text_from_file(file_like_object)
        
        if "Error:" in resume_text:
            analysis_string = resume_text
            return {"messages": [AIMessage(content=analysis_string)], "next": "supervisor"}
        else:
            analysis_string = resume_analyzer_agent.invoke({"resume_text": resume_text})
            # Also, clear the file_data from the state after processing
            return {
                "messages": [AIMessage(content=analysis_string)],
                "resume_text": resume_text,
                "file_data": None, # <-- Clear the data
                "next": "supervisor"
            }
    else:
        # This block now handles the case where the user asks to analyze
        # a resume without having uploaded one first.
        analysis_string = "It looks like you want me to analyze a resume, but I don't see one. Please use the sidebar to upload your file first."
        return {"messages": [AIMessage(content=analysis_string)], "next": "supervisor"}
    

def resume_qa_node(state: AgentState) -> dict:
    print("---AGENT: ResumeQAAgent---")
    
    # Get the resume text from the state
    resume_context = state.get("resume_text")
    question = state["messages"][-1].content
    
    if not resume_context:
        # This is a safety net in case the agent is called incorrectly
        answer_string = "It looks like you're asking about a resume, but one hasn't been analyzed yet. Please upload a resume first."
    else:
        answer_string = resume_qa_agent.invoke({
            "resume_context": resume_context,
            "question": question
        })
        
    return {"messages": [AIMessage(content=answer_string)], "next": "supervisor"}

# --- 4. Assemble the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("ResumeAnalyst", resume_analyzer_node)
workflow.add_node("CareerAdvisor", career_advisor_node)
workflow.add_node("LearningPath", learning_path_node)
workflow.add_node("JobSearch", job_search_node)
workflow.add_node("ResumeQAAgent", resume_qa_node) 


# --- THIS IS THE CORRECTED WIRING ---
# A single router function reads the 'next' field from the state
def router(state: AgentState):
    return state.get("next", "END")

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "ResumeAnalyst": "ResumeAnalyst",
        "ResumeQAAgent": "ResumeQAAgent",
        "CareerAdvisor": "CareerAdvisor",
        "LearningPath": "LearningPath",
        "JobSearch": "JobSearch", # This route is correct
        "END": END
    }
)

# Add the edges back to the supervisor for all agents.
workflow.add_edge("ResumeAnalyst", "supervisor")
workflow.add_edge("CareerAdvisor", "supervisor")
workflow.add_edge("LearningPath", "supervisor")
workflow.add_edge("JobSearch", "supervisor") 
workflow.add_edge("ResumeQAAgent", "supervisor")
app = workflow.compile()
print("--- Backend App with Job Search Agent Compiled ---")