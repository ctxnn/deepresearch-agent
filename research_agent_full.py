
"""
Full Multi-Agent Research System

This module integrates all components of the research system:
- User clarification and scoping
- Research brief generation  
- Multi-agent research coordination
- Final report generation

The system orchestrates the complete research workflow from initial user
input through final report delivery.
"""

import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from reisearch.utils import get_today_str
from reisearch.prompts import final_report_generation_prompt
from reisearch.state_scope import AgentState, AgentInputState
from reisearch.research_agent_scope import clarify_with_user, write_research_brief
from reisearch.multi_agent_supervisor import supervisor_agent

# ===== Config =====

from langchain.chat_models import init_chat_model
writer_model = init_chat_model(model="groq:openai/gpt-oss-20b")

# ===== FINAL REPORT GENERATION =====

from reisearch.state_scope import AgentState

async def final_report_generation(state: AgentState):
    """
    Final report generation node.

    Synthesizes all research findings into a comprehensive final report
    """

    notes = state.get("notes", [])

    findings = "\n".join(notes)

    final_report_prompt = final_report_generation_prompt.format(
        research_brief=state.get("research_brief", ""),
        findings=findings,
        date=get_today_str()
    )

    system_instruction = (
        "You are a professional report writer. You do NOT have access to any tools, commands, "
        "or external search engines. You must write the final report using ONLY the provided findings. "
        "Do NOT attempt to invoke any tools or output JSON function calls."
    )

    last_err = None
    final_report = None
    for attempt in range(3):
        try:
            final_report = await writer_model.ainvoke([
                SystemMessage(content=system_instruction),
                HumanMessage(content=final_report_prompt)
            ])
            break
        except Exception as e:
            last_err = e
            if attempt < 2:
                await asyncio.sleep(2.0 * (attempt + 1))
    else:
        raise last_err

    return {
        "final_report": final_report.content, 
        "messages": ["Here is the final report: " + final_report.content],
    }


# ===== GRAPH CONSTRUCTION =====
# Build the overall workflow
deep_researcher_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Add workflow nodes
deep_researcher_builder.add_node("clarify_with_user", clarify_with_user)
deep_researcher_builder.add_node("write_research_brief", write_research_brief)
deep_researcher_builder.add_node("supervisor_subgraph", supervisor_agent)
deep_researcher_builder.add_node("final_report_generation", final_report_generation)

# Add workflow edges
deep_researcher_builder.add_edge(START, "clarify_with_user")
deep_researcher_builder.add_edge("write_research_brief", "supervisor_subgraph")
deep_researcher_builder.add_edge("supervisor_subgraph", "final_report_generation")
deep_researcher_builder.add_edge("final_report_generation", END)

# Compile the full workflow with memory checkpointer
agent = deep_researcher_builder.compile(checkpointer=MemorySaver())
