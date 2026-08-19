# app/langgraph_core/graph.py

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from app.langgraph_core.nodes import (
    AgentState,
    supervisor_node,
    resume_analyzer_node,
    resume_qa_node,
    career_advisor_node,
    learning_path_node,
    job_search_node
)

# 1. Initialize StateGraph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("ResumeAnalyst", resume_analyzer_node)
workflow.add_node("ResumeQAAgent", resume_qa_node)
workflow.add_node("CareerAdvisor", career_advisor_node)
workflow.add_node("LearningPath", learning_path_node)
workflow.add_node("JobSearch", job_search_node)

# Irrelevant query handling node
def irrelevant_node(state: AgentState) -> dict:
    return {
        "messages": [
            AIMessage(
                content="I am a career assistant and can only help with career-related questions. How can I assist you today?"
            )
        ]
    }

workflow.add_node("IRRELEVANT", irrelevant_node)

# 3. Entry point
workflow.set_entry_point("supervisor")

# 4. Routing logic
def router(state: AgentState):
    return state.get("next", "END")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "ResumeAnalyst": "ResumeAnalyst",
        "ResumeQAAgent": "ResumeQAAgent",
        "CareerAdvisor": "CareerAdvisor",
        "LearningPath": "LearningPath",
        "JobSearch": "JobSearch",
        "IRRELEVANT": "IRRELEVANT",
        "END": END
    }
)

# 5. Connect workers back to supervisor
workflow.add_edge("ResumeAnalyst", "supervisor")
workflow.add_edge("ResumeQAAgent", "supervisor")
workflow.add_edge("CareerAdvisor", "supervisor")
workflow.add_edge("LearningPath", "supervisor")
workflow.add_edge("JobSearch", "supervisor")
workflow.add_edge("IRRELEVANT", END)

# 6. Compile the final application graph
app = workflow.compile()
print("--- Backend App with Corrected Graph Logic Compiled ---")
