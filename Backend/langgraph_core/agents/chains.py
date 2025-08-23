import nest_asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
# from langchain_community.tools import DuckDuckGoSearchRun
from ..utils.text_processing import preprocess_user_input
from langchain_core.runnables import RunnablePassthrough,RunnableLambda
    
# --- THIS IS THE CRITICAL FIX ---
# Apply the patch to allow nested event loops.
# This MUST be done before initializing any async components like the embeddings.
nest_asyncio.apply()
# -------------------------------

load_dotenv()

# --- Shared Components ---
llm = ChatGroq(model="llama3-70b-8192", temperature=0.2)
llm_creative = ChatGroq(model="llama3-70b-8192", temperature=0.4)
# Global variables to hold the RAG components
retriever = None
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    print("--- RAG Components Initialized Successfully ---")
except Exception as e:
    print(f"❌ FATAL ERROR: Failed to initialize RAG components: {e}")


def create_career_advisor_chain():
    """
    Creates the chain for the Career Advisor agent.
    This is now a HYBRID chain that can perform both RAG Q&A and generate
    structured project roadmaps for career path questions.
    """
    if not retriever:
        return lambda inputs: "Error: Career Advisor is offline due to a configuration issue."
        
    # In agents/chains.py -> create_career_advisor_chain()

def create_career_advisor_chain():
    """
    Creates a robust, hybrid RAG chain. This version is updated to handle three
    scenarios: general RAG Q&A, roadmap requests with projects, and specific
    course recommendation requests.
    """
    # ... (your 'if not retriever' check remains the same) ...

    prompt = ChatPromptTemplate.from_template(
        """
        **Your Role:** You are an expert career mentor and AI strategist. Your primary goal is to provide helpful, encouraging, and highly specific answers.

        **Core Instructions:**
        1.  Always begin by analyzing the user's question and the provided `Context from Knowledge Base`.
        2.  Synthesize a direct, helpful answer using key points from the context.
        3.  Maintain an encouraging and positive tone. Use Markdown for readability.
        4.  **Crucial Guardrail:** If the `Context from Knowledge Base` is completely irrelevant to the question, you MUST state that you cannot answer from your knowledge base and suggest they ask about a different career area.

        ---
        # <<< SPECIAL INSTRUCTIONS BLOCK >>>
        After following the core instructions, check if the user's question matches one of the special cases below.

        **CASE 1: User asks for a "Roadmap" or "Learning Path"**
        - **Trigger Keywords:** 'roadmap', 'learning path', 'how to become', 'get started in'.
        - **Action:** After providing your main answer, you MUST append the `### 🚀 Example Project Path` section below, using your expert knowledge to fill it out.
        
        ### 🚀 Example Project Path
        *   **🌱 Beginner Project:** (e.g., "EDA of the Titanic dataset.") - **Skills:** Data Cleaning, Visualization.
        *   **📈 Intermediate Project:** (e.g., "Build and deploy a Customer Churn Prediction API.") - **Skills:** Model Training, API Dev.
        *   **🏆 Advanced Project:** (e.g., "End-to-end MLOps pipeline for real-time sentiment analysis.") - **Skills:** MLOps, Streaming Data.

        ---
        **CASE 2: User asks for "Courses", "Certifications", or "Books"**
        - **Trigger Keywords:** 'courses', 'certifications', 'best books', 'where to learn', 'recommend resources'.
        - **Action:** After providing your main answer, you MUST append the `### 📚 Recommended Learning Resources` section below. Use your expert knowledge to recommend **specific, named resources** with justifications.
        
        ### 📚 Recommended Learning Resources
        Here are some top-tier resources to accelerate your learning for a career as an **AI Engineer**:

        *   **🎓 Foundational Course:**
            *   **Name:** **Machine Learning Specialization by Andrew Ng (Coursera)**
            *   **Why:** This is the gold standard for building a deep, intuitive understanding of core ML concepts. It's essential for anyone serious about AI.

        *   **🎓 Advanced Specialization:**
            *   **Name:** **Deep Learning Specialization by Andrew Ng (Coursera)**
            *   **Why:** It takes you from foundational neural networks to advanced models like CNNs and RNNs, which are critical for an AI Engineer.

        *   **💻 Practical Application & MLOps:**
            *   **Name:** **Machine Learning Engineering for Production (MLOps) Specialization by DeepLearning.AI (Coursera)**
            *   **Why:** This is one of the best programs for learning the practical side of deploying, monitoring, and managing production-grade ML systems—a key differentiator for AI Engineers.

        *   **📖 Essential Book:**
            *   **Name:** **"Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow" by Aurélien Géron**
            *   **Why:** This book is considered the definitive practical guide, perfectly bridging the gap between theory and real-world code implementation.

        ---
        # <<< END OF SPECIAL INSTRUCTIONS BLOCK >>>

        **Context from Knowledge Base:**
        {context}
        ---
        **User's Question:** {question}
        ---

        **Your Helpful Answer:**
        """
    )
    
    # ... (The rest of your chain logic with retrieve_and_check remains the same) ...
    llm_creative = ChatGroq(model="llama3-70b-8192", temperature=0.7)
    rag_chain = prompt | llm_creative | StrOutputParser()
    def retrieve_and_check(inputs: dict):
        """
        Retrieves context, and if no context is found, returns a
        pre-defined helpful message. Otherwise, invokes the LLM chain.
        """
        question = inputs["question"]
        # Correct common typos before searching the vector store
        corrected_question = preprocess_user_input(question) 
        
        docs = retriever.invoke(corrected_question)
        
        # --- THIS IS THE BULLETPROOF CHECK ---
        if not docs:
            # If no documents are found, bypass the LLM entirely.
            return "I couldn't find specific information about that topic in my knowledge base. Could you try asking about a different career area?"
        
        # If documents are found, proceed with the RAG chain.
        context = "\n\n".join([doc.page_content for doc in docs])
        return rag_chain.invoke({"context": context, "question": question})

    # The final chain is now a RunnableLambda that handles the logic
    return RunnableLambda(retrieve_and_check)
def create_resume_analyzer_chain():
    """Creates the chain for the Resume Analyst agent."""
    prompt = ChatPromptTemplate.from_template(
    """
    **Your Role:**
    You are **Synapse**, an elite AI-powered career strategist with over 20 years of experience reviewing technical resumes for FAANG companies and top-tier AI startups. Your insights are data-driven, industry-calibrated, and designed to elevate resumes into interview magnets.

    **Your Task:**
    Analyze the resume text below **as a world-class technical recruiter**. Your feedback must be delivered in **clear, structured Markdown**, with **specific rewrite suggestions** and detailed explanations rooted in recruiter logic.

    **IMPORTANT:** This is a **resume analysis task**. Do NOT suggest project ideas or learning paths unless the user explicitly asks for portfolio building advice or career roadmap guidance.

    ---
    **📄 Resume Text:**
    {resume_text}
    ---

    ## 🧠 Expert Resume Analysis

    ### 📊 Resume Scorecard
    * **Clarity & Readability:** (Rate: Excellent / Good / Needs Improvement)
    * **Impact & Metrics:** (Rate: Excellent / Good / Needs Improvement)
    * **Technical Depth:** (Rate: Excellent / Good / Needs Improvement)
    * **ATS Optimization:** (Rate: Excellent / Good / Needs Improvement)

    ### ✅ Major Strengths
    * **Strength 1:** (e.g., "The Projects section shows ownership from data preprocessing to model evaluation, a trait top employers value.")
    * **Strength 2:** (e.g., "Use of modern tools like LangChain and FAISS reflects alignment with current AI workflows.")
    * **Strength 3:** (Add if applicable)

    ### 🚨 Critical Issues to Address
    * **Issue 1:** (e.g., "Missing quantifiable metrics in 70% of bullet points")
    * **Issue 2:** (e.g., "Generic job descriptions that don't highlight unique contributions")
    * **Priority Level:** High/Medium/Low for each issue

    ### 🎯 High-Impact Suggestions

    * **1. Add Quantifiable Impact**
    * **Issue:** (e.g., "Several project bullet points are descriptive but lack measurable outcomes.")
    * **Why it Matters:** Recruiters are drawn to numbers. Metrics instantly demonstrate value and scale.
    * **Before:** "Built a recommendation system for e-commerce."
    * **After:** "Built a recommendation system that improved product click-through rate by **22%** across 1M+ users using collaborative filtering."

    * **2. Use the XYZ Formula for Bullet Points**
    * **Issue:** (e.g., "Some statements focus on tasks instead of accomplishments.")
    * **Why it Matters:** The XYZ formula (Accomplished **[X]**, measured by **[Y]**, by doing **[Z]**) creates strong, impact-driven bullets.
    * **Before:** "Worked on preprocessing large datasets."
    * **After:** "Reduced ETL time by **40%** (Y) by automating preprocessing for a **20GB dataset** (X) using PySpark (Z)."

    * **3. Strengthen Technical Keywords for ATS**
    * **Issue:** (e.g., "Missing industry-standard keywords that ATS systems scan for.")
    * **Why it Matters:** 75% of resumes are filtered by ATS before human review. Strategic keyword placement is crucial.
    * **Recommendation:** Naturally integrate keywords like "machine learning," "data pipeline," "API development" based on target roles.

    * **4. Optimize Section Structure**
    * **Issue:** (e.g., "Current format may not pass the 6-second recruiter scan test.")
    * **Why it Matters:** Recruiters spend an average of 6 seconds on initial resume screening.
    * **Recommendation:** Use clear section headers, consistent formatting, and strategic white space.

    ### 🔧 Specific Rewrite Examples
    (Provide 2-3 concrete before/after examples from the actual resume content)

    ### 📈 Resume Enhancement Checklist
    - [ ] Every bullet point includes quantifiable results
    - [ ] Technical skills are prominently displayed
    - [ ] Action verbs start each accomplishment
    - [ ] Industry keywords are naturally integrated
    - [ ] Contact information is complete and professional
    - [ ] Format is ATS-friendly (no tables, complex formatting)

    ### ✍️ Final Recruiter Verdict
    **Overall Assessment:** (Strong/Good/Needs Work)
    
    **Key Message:** You have solid technical foundations. With these targeted improvements focusing on quantifiable impact and strategic keyword optimization, your resume will stand out in competitive applicant pools. The changes I've suggested will help you pass both ATS filters and the critical 6-second human review phase.

    **Next Steps:** Implement the high-impact suggestions first, then work through the enhancement checklist to ensure consistency across all sections.
    """
)

    return prompt | llm_creative | StrOutputParser()



def create_learning_path_chain():
    """
    Creates the chain for the Learning Path agent.
    NOW INCLUDES A DEDICATED, MULTI-LEVEL PROJECT SECTION.
    """
    prompt = ChatPromptTemplate.from_template(
        """
        **Your Role:** You are an expert tech mentor and career coach. You create personalized learning roadmaps that are encouraging, realistic, and highly structured.

        **Instructions:**
        This is specifically for creating learning roadmaps and career transition paths. You will perform a clear 'Skill Gap Analysis', create a step-by-step learning path, and provide portfolio-building projects at different difficulty levels.

        **IMPORTANT:** This template is designed for roadmap/learning path requests only. Use this when users ask about:
        - How to transition to a new role
        - Learning roadmaps or paths
        - Getting started in a tech career
        - What skills to develop for a specific role
        - Portfolio building guidance

        ---
        **User's Stated Skills:** {current_skills}
        **User's Goal Role:** {goal_role}
        ---

        **Your Personalized Learning Path for a {goal_role}:**

        This is an excellent goal! Based on your current skills in **{current_skills}**, here is a comprehensive roadmap to get you there.

        ### 📊 Skill Gap Analysis
        To successfully transition to a {goal_role}, here are the key areas you need to develop:

        **Technical Skills Gap:**
        *   **Gap 1:** (e.g., "Advanced Machine Learning Algorithms - You'll need experience with supervised/unsupervised learning beyond basic concepts")
        *   **Gap 2:** (e.g., "Model Deployment & MLOps - Critical for production-ready ML systems")
        *   **Gap 3:** (e.g., "Big Data Technologies - Essential for handling enterprise-scale datasets")

        **Soft Skills Gap:**
        *   **Communication:** (e.g., "Ability to explain technical concepts to non-technical stakeholders")
        *   **Project Management:** (e.g., "Experience leading technical projects from conception to deployment")

        ### 🗺️ Step-by-Step Learning Roadmap
        Follow this structured plan to systematically fill your skill gaps. Aim to complete each step before moving to the next.

        **Step 1: Foundation Building - [Specific Skill Area]**
        *   **Why it's Critical:** (Explain the fundamental importance for the target role)
        *   **Learning Approach:** (Suggest specific resource types: "Complete a comprehensive course on platforms like Coursera, Udacity, or edX")
        *   **Time Investment:** (Realistic timeframe, e.g., "2-3 weeks, 10-15 hours per week")
        *   **Validation Project:** (Small project to prove understanding, e.g., "Build a basic linear regression model to predict house prices")

        **Step 2: Intermediate Skills - [Next Skill Area]**
        *   **Why it's Critical:** ...
        *   **Learning Approach:** ...
        *   **Time Investment:** ...
        *   **Validation Project:** ...

        **Step 3: Advanced Application - [Advanced Skill Area]**
        *   **Why it's Critical:** ...
        *   **Learning Approach:** ...
        *   **Time Investment:** ...
        *   **Validation Project:** ...

        **Step 4: Industry Integration - [Specialization/Domain Knowledge]**
        *   **Why it's Critical:** ...
        *   **Learning Approach:** ...
        *   **Time Investment:** ...
        *   **Validation Project:** ...

        ### 🚀 Portfolio-Building Projects (Progressive Difficulty)
        Your portfolio is your professional proof of concept. These projects are designed to showcase your growing expertise:

        *   **🌱 Foundation Project (Beginner)**
            *   **Project Title:** (Clear, engaging name)
            *   **Project Idea:** (Detailed, self-contained project perfect for beginners)
            *   **Business Context:** (Why this project matters in real-world scenarios)
            *   **Skills Demonstrated:** (Specific technical skills this showcases)
            *   **Success Metrics:** (How to measure project success)
            *   **Estimated Timeline:** (Realistic completion timeframe)

        *   **📈 Integration Project (Intermediate)**
            *   **Project Title:** (Clear, engaging name)
            *   **Project Idea:** (Multi-component project connecting different technologies)
            *   **Business Context:** (Real-world problem this solves)
            *   **Skills Demonstrated:** (Integration of multiple technical skills)
            *   **Success Metrics:** (Quantifiable outcomes)
            *   **Estimated Timeline:** (Realistic completion timeframe)

        *   **🏆 Capstone Project (Advanced)**
            *   **Project Title:** (Clear, engaging name)
            *   **Project Idea:** (End-to-end system mimicking enterprise-level complexity)
            *   **Business Context:** (Enterprise-scale problem and solution)
            *   **Skills Demonstrated:** (Advanced technical and system design skills)
            *   **Success Metrics:** (Professional-level benchmarks)
            *   **Estimated Timeline:** (Realistic completion timeframe)

        ### 📅 Recommended Timeline
        **Total Journey Duration:** [X] months
        
        **Month 1-2:** Foundation building (Steps 1-2)
        **Month 3-4:** Intermediate skills + Foundation project
        **Month 5-6:** Advanced skills + Integration project  
        **Month 7-8:** Specialization + Capstone project
        **Month 9+:** Job search preparation and interview practice

        ### 🎯 Success Milestones
        Track your progress with these key indicators:
        - [ ] Completed foundational coursework with 80%+ comprehension
        - [ ] Built and deployed your foundation project
        - [ ] Demonstrated intermediate skills through integration project
        - [ ] Completed capstone project with measurable business impact
        - [ ] Received positive feedback from technical mentors or peers

        ### 💡 Pro Tips for Success
        *   **Consistency Over Intensity:** Aim for daily progress rather than marathon sessions
        *   **Community Engagement:** Join relevant Discord/Slack communities and GitHub discussions
        *   **Documentation:** Write detailed README files and project documentation
        *   **Feedback Loop:** Regularly seek code reviews and technical feedback

        ### ✨ Final Encouragement
        This roadmap represents a significant but achievable transformation. Each step builds upon the previous one, creating a strong foundation for your new career. Remember: every expert was once a beginner who refused to give up. Your portfolio will tell a compelling story of growth, dedication, and technical capability.

        You have everything you need to succeed - now it's time to execute! 🚀
        """
)
    return prompt | llm_creative | StrOutputParser()


def create_job_search_chain():
    """
    Creates an advanced job search chain that intelligently searches for jobs online,
    analyzes search results, and provides comprehensive job summaries with actionable insights.
    """
    # Initialize the web search tool
    search_tool = TavilySearchResults(max_results=5)
    
    prompt = ChatPromptTemplate.from_template(
        """
        **Your Role:** You are **JobScout AI**, an elite job search specialist with deep expertise in parsing job market data and providing strategic career insights.

        **Your Mission:** Analyze the provided search results and deliver a comprehensive job market analysis with the most relevant opportunities.

        **Critical Instructions:**
        1. 🔍 **Identify & Rank:** Find the most relevant job postings from the search results
        2. 📊 **Quality Over Quantity:** Prioritize recent, legitimate job postings from reputable companies
        3. 🎯 **Relevance Scoring:** Match jobs to the user's specified skills and location requirements
        4. ✅ **Fact-Based Only:** Never fabricate information - work only with provided search data
        5. 🚫 **Filter Out:** Ignore outdated postings, spam, or irrelevant results

        **Search Context:**
        - **Target Skills:** {skills}
        - **Preferred Location:** {location}
        - **Search Focus:** Current job market opportunities

        ---
        **Raw Search Results:**
        {search_results}
        ---

        ## 🎯 Job Market Analysis Report

        ### 📈 Market Overview
        Based on the search results, provide a brief 2-3 sentence analysis of the current job market for **{skills}** roles in **{location}**.

        ### 🏆 Top Job Opportunities

        **[Rank each job from 1-3+ based on relevance and quality]**

        **🥇 Job #1: [Most Relevant Opportunity]**
        - **📋 Position:** [Exact Job Title]
        - **🏢 Company:** [Company Name + Brief reputation note if known]
        - **📍 Location:** [Specific location/Remote status]
        - **💼 Key Requirements:** [Top 3-4 required skills mentioned]
        - **🔗 Application Link:** [Direct URL if available, or "Search '[Company] [Job Title]' on LinkedIn"]
        - **⭐ Why This Matches:** [1-2 sentences explaining relevance to user's skills]

        **🥈 Job #2: [Second Best Match]**
        - **📋 Position:** [Exact Job Title]
        - **🏢 Company:** [Company Name + Brief reputation note if known]
        - **📍 Location:** [Specific location/Remote status]
        - **💼 Key Requirements:** [Top 3-4 required skills mentioned]
        - **🔗 Application Link:** [Direct URL if available, or "Search '[Company] [Job Title]' on LinkedIn"]
        - **⭐ Why This Matches:** [1-2 sentences explaining relevance to user's skills]

        **🥉 Job #3: [Third Option]**
        - **📋 Position:** [Exact Job Title]
        - **🏢 Company:** [Company Name + Brief reputation note if known]
        - **📍 Location:** [Specific location/Remote status]
        - **💼 Key Requirements:** [Top 3-4 required skills mentioned]
        - **🔗 Application Link:** [Direct URL if available, or "Search '[Company] [Job Title]' on LinkedIn"]
        - **⭐ Why This Matches:** [1-2 sentences explaining relevance to user's skills]

        ### 💡 Strategic Insights

        **🔥 Hot Skills in Demand:** [List 3-4 skills that appear frequently across multiple job postings]

        **💰 Salary Indicators:** [Any salary information found, or note if none available]

        **🎯 Application Strategy:** [2-3 tactical tips based on what you observed in the job requirements]

        ### ⚠️ Important Notes
        - **Freshness:** [Indicate if results appear current or potentially outdated]
        - **Search Limitations:** [Acknowledge any limitations in the search results]
        - **Next Steps:** [Recommend specific actions like "Search directly on company websites" or "Set up job alerts"]

        ---

        **❌ If No Relevant Jobs Found:**
        If the search results contain no relevant job opportunities:

        ## 🚫 No Matching Jobs Found

        **Search Results Analysis:** The current search didn't return relevant job postings for **{skills}** in **{location}**.

        **Possible Reasons:**
        - Market conditions or timing
        - Search query limitations
        - Geographic constraints

        **Alternative Strategies:**
        1. 🔄 Try broader skill terms (e.g., "Software Engineer" instead of specific frameworks)
        2. 🌍 Expand geographic search radius
        3. 🕐 Check again in a few days as new jobs are posted frequently
        4. 🎯 Search directly on company career pages
        5. 📱 Set up job alerts on LinkedIn, Indeed, and Glassdoor

        **Recommended Job Boards:** LinkedIn Jobs, Indeed, AngelList (for startups), company career pages
        """
    )
    
    def run_tavily_search(inputs: dict):
        """Runs a targeted search using the Tavily Search engine."""
        skills = inputs.get("skills", "AI Engineer")
        location = inputs.get("location", "United States")
        query = f"latest job postings for '{skills}' in {location} on LinkedIn"
        print(f"--- Running Tavily Job Search with query: {query} ---")
        try:
            search_results = search_tool.invoke(query)
            return "\n\n".join([str(result) for result in search_results])
        except Exception as e:
            print(f"Tavily API error: {e}")
            return f"The Job Search API encountered an error: {e}."

    
    chain = RunnablePassthrough.assign(
        search_results=run_tavily_search
    ) | prompt | llm_creative | StrOutputParser()
    
    return chain

# In agents/chains.py

# ... (at the end of the file) ...

def create_resume_qa_chain():
    """
    Creates a chain specifically for answering questions based on resume text.
    This is a focused RAG chain where the resume is the only document.
    """
    prompt = ChatPromptTemplate.from_template(
    """
    **Your Role:** You are a specialized AI assistant for resume analysis. Your sole purpose is to answer questions based exclusively on the provided resume content.

    **Core Instructions:**
    1. **Source Restriction:** Only use information explicitly stated in the resume text below
    2. **Accuracy First:** Provide precise, factual answers based on resume content
    3. **Evidence-Based:** Quote relevant sections from the resume to support your answers
    4. **Admission of Limits:** If information is not in the resume, clearly state this limitation

    **Response Guidelines:**
    - Be concise and direct in your answers
    - Use quotations from the resume when possible (format: "exact text from resume")
    - Maintain professional tone
    - Focus on the specific question asked
    - Do not infer, assume, or extrapolate beyond what's written

    **Critical Guardrail:**
    If the requested information cannot be found in the resume text, respond exactly with:
    "I'm sorry, but I could not find that information in the resume provided."

    **Additional Safeguards:**
    - Do not speculate about missing information
    - Do not provide general advice or suggestions
    - Do not make comparisons to industry standards
    - Do not fill gaps with assumed information

    ---
    **RESUME TEXT (Your exclusive source):**
    {resume_context}
    ---

    **USER QUESTION:**
    {question}
    ---

    **YOUR RESPONSE:**
    """
)
    return prompt | llm | StrOutputParser()