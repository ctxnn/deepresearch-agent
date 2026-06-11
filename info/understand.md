# 🔬 Reisearch — Complete Deep Dive

> A deep research multi-agent system built with LangGraph that takes a user's question, clarifies it, breaks it into sub-topics, researches each in parallel using web search, and generates a comprehensive final report.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [How the Full Pipeline Works](#2-how-the-full-pipeline-works)
3. [State Definitions](#3-state-definitions)
   - [state_scope.py — Main Agent State](#31-state_scopepy--main-agent-state)
   - [state_research.py — Researcher State](#32-state_researchpy--researcher-state)
   - [state_multi_agent_supervisor.py — Supervisor State](#33-state_multi_agent_supervisorpy--supervisor-state)
4. [Utilities & Tools](#4-utilities--tools)
   - [utils.py — Search, Summarization & Tools](#41-utilspy--search-summarization--tools)
5. [Prompt Templates](#5-prompt-templates)
   - [prompts.py — All System Prompts](#51-promptspy--all-system-prompts)
6. [Research Agent (Single Agent)](#6-research-agent-single-agent)
   - [research_agent.py — Web Search Agent](#61-research_agentpy--web-search-agent)
7. [Research Agent MCP (File-Based Variant)](#7-research-agent-mcp-file-based-variant)
   - [research_agent_mcp.py — MCP Agent](#71-research_agent_mcppy--mcp-agent)
8. [Research Scoping Agent](#8-research-scoping-agent)
   - [research_agent_scope.py — Clarify & Brief](#81-research_agent_scopepy--clarify--brief)
9. [Multi-Agent Supervisor](#9-multi-agent-supervisor)
   - [multi_agent_supervisor.py — Parallel Coordination](#91-multi_agent_supervisorpy--parallel-coordination)
10. [Full Pipeline](#10-full-pipeline)
    - [research_agent_full.py — End-to-End Workflow](#101-research_agent_fullpy--end-to-end-workflow)
11. [Configuration & Environment](#11-configuration--environment)
12. [Execution Flow Walkthrough](#12-execution-flow-walkthrough)

---

## 1. Architecture Overview

The system follows a **hierarchical multi-agent pattern**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL PIPELINE (research_agent_full.py)        │
│                                                                  │
│  ┌──────────────┐   ┌───────────────┐   ┌────────────────────┐  │
│  │  STEP 1:     │   │  STEP 2:      │   │  STEP 3:           │  │
│  │  Clarify     │──▶│  Write Brief  │──▶│  Supervisor        │  │
│  │  with User   │   │               │   │  Subgraph          │  │
│  └──────────────┘   └───────────────┘   └────────┬───────────┘  │
│                                                   │              │
│                                          ┌────────▼───────────┐  │
│                                          │  STEP 4:           │  │
│                                          │  Final Report      │  │
│                                          │  Generation        │  │
│                                          └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │  SUPERVISOR         │
                    │  (multi_agent_      │
                    │   supervisor.py)    │
                    └────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │ Researcher │ │ Researcher │ │ Researcher │
        │  Agent 1   │ │  Agent 2   │ │  Agent 3   │
        │ (research_ │ │ (research_ │ │ (research_ │
        │  agent.py) │ │  agent.py) │ │  agent.py) │
        └────────────┘ └────────────┘ └────────────┘
              │              │              │
        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │  Tavily    │ │  Tavily    │ │  Tavily    │
        │  Web Search│ │  Web Search│ │  Web Search│
        └────────────┘ └────────────┘ └────────────┘
```

### Key Concepts

| Concept | What it means |
|---|---|
| **LangGraph** | A framework for building stateful, multi-step agent workflows as directed graphs |
| **StateGraph** | A graph where each node reads/writes to a shared state dictionary |
| **Node** | A Python function that performs work (LLM call, tool execution, etc.) |
| **Edge** | A connection between nodes — can be fixed or conditional |
| **Subgraph** | A compiled graph used as a node inside another graph |
| **Tool Calling** | LLMs can "call" tools by outputting structured JSON; the system executes them |
| **Supervisor Pattern** | One agent delegates tasks to worker agents and aggregates results |

---

## 2. How the Full Pipeline Works

Here's what happens when a user submits a question like *"Compare React vs Vue vs Svelte for building dashboards"*:

```
User: "Compare React vs Vue vs Svelte for building dashboards"
         │
         ▼
   ┌─────────────────────┐
   │  1. CLARIFY          │  Does the user need to provide more info?
   │     with User        │  → No, question is clear enough
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  2. WRITE BRIEF      │  Convert chat into a detailed research brief:
   │                      │  "Compare React, Vue, and Svelte frameworks
   │                      │   for dashboard development, covering
   │                      │   performance, ecosystem, learning curve..."
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  3. SUPERVISOR       │  Decides to run 3 parallel agents:
   │     thinks...        │  - Agent 1: "Research React for dashboards"
   │                      │  - Agent 2: "Research Vue for dashboards"
   │                      │  - Agent 3: "Research Svelte for dashboards"
   └──────────┬──────────┘
              │
              ├──▶ Agent 1: searches web → compresses findings
              ├──▶ Agent 2: searches web → compresses findings
              └──▶ Agent 3: searches web → compresses findings
              │
              ▼
   ┌─────────────────────┐
   │  Supervisor reviews   │  Checks: Do I have enough? 
   │  all findings         │  → Yes → calls ResearchComplete
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  4. FINAL REPORT     │  Takes all compressed research from all
   │     GENERATION       │  agents and writes a comprehensive
   │                      │  markdown report with citations
   └──────────┬──────────┘
              │
              ▼
   📄 Final Report (markdown with headings, citations, sources)
```

---

## 3. State Definitions

State is the **shared memory** that flows through the graph. Each node reads from it and writes updates back. LangGraph merges updates automatically using **reducers** (like `add_messages` for appending messages, `operator.add` for concatenating lists).

### 3.1 `state_scope.py` — Main Agent State

This file defines the **top-level state** for the entire pipeline, plus Pydantic schemas for structured LLM output.

```python
"""State Definitions and Pydantic Schemas for Research Scoping.

This defines the state objects and structured schemas used for
the research agent scoping workflow, including researcher state management and output schemas.
"""

import operator
from typing_extensions import Optional, Annotated, List, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
```

**Imports explained:**
- `operator.add` — Used as a **reducer** to concatenate lists when state is updated. If two nodes both add notes, they get merged into one list.
- `Annotated` — Python typing feature used to attach metadata (like reducers) to type hints.
- `MessagesState` — A built-in LangGraph state class that has a `messages` field with `add_messages` reducer built in.
- `add_messages` — A special reducer that appends new messages to the existing list (instead of replacing them).
- `BaseModel, Field` — Pydantic classes for defining structured output schemas that the LLM must conform to.

#### `AgentInputState` — What the user provides

```python
class AgentInputState(MessagesState):
    """Input state for the full agent - only contains messages from user input."""
    pass
```

This is the **input schema** — it restricts what the user can pass in. By extending `MessagesState`, it only accepts a `messages` list. This prevents users from accidentally setting internal fields like `research_brief` or `final_report`.

**Why separate input/output schemas?** LangGraph lets you define:
- `input_schema`: What the graph accepts as input
- `output_schema`: What the graph returns as output
- The full state (used internally) can have more fields than either

#### `AgentState` — The full internal state

```python
class AgentState(MessagesState):
    """
    Main state for the full multi-agent research system.

    Extends MessagesState with additional fields for research coordination.
    Note: Some fields are duplicated across different state classes for proper
    state management between subgraphs and the main workflow.
    """

    # Research brief generated from user conversation history
    research_brief: Optional[str]
    # Messages exchanged with the supervisor agent for coordination
    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages]
    # Raw unprocessed research notes collected during the research phase
    raw_notes: Annotated[list[str], operator.add] = []
    # Processed and structured notes ready for report generation
    notes: Annotated[list[str], operator.add] = []
    # Final formatted research report
    final_report: str
```

**Field-by-field breakdown:**

| Field | Type | Reducer | Purpose |
|---|---|---|---|
| `messages` | `list[BaseMessage]` | `add_messages` | Inherited from `MessagesState`. User conversation history. |
| `research_brief` | `Optional[str]` | None (replace) | The detailed research question generated from user chat. |
| `supervisor_messages` | `Sequence[BaseMessage]` | `add_messages` | Internal messages between supervisor and sub-agents. |
| `raw_notes` | `list[str]` | `operator.add` | Raw text from all tool calls and AI responses. |
| `notes` | `list[str]` | `operator.add` | Cleaned/compressed research notes from sub-agents. |
| `final_report` | `str` | None (replace) | The final markdown report. |

**What is a reducer?** When a node returns `{"notes": ["new note"]}`, the reducer determines how to merge it with the existing state:
- `operator.add`: Concatenates → `["old note"] + ["new note"]` = `["old note", "new note"]`
- `add_messages`: Appends messages intelligently (handles message IDs, dedup, etc.)
- No reducer: The new value **replaces** the old value entirely

#### Structured Output Schemas

```python
class ClarifyWithUser(BaseModel):
    """Schema for user clarification decision and questions."""

    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )
```

When you call `model.with_structured_output(ClarifyWithUser)`, the LLM is forced to return a JSON object matching this exact schema. This eliminates parsing errors and ensures deterministic routing.

**Example LLM output:**
```json
{
  "need_clarification": false,
  "question": "",
  "verification": "I have enough information. I'll begin researching React vs Vue vs Svelte for dashboards."
}
```

```python
class ResearchQuestion(BaseModel):
    """Schema for structured research brief generation."""

    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )
```

This forces the LLM to output a single `research_brief` string — a detailed, well-scoped research question derived from the user conversation.

---

### 3.2 `state_research.py` — Researcher State

This file defines state for the **individual research agents** (the workers), plus some shared Pydantic schemas.

```python
"""
State Definitions and Pydantic Schemas for Research Agent

This module defines the state objects and structured schemas used for
the research agent workflow, including researcher state management and output schemas.
"""

import operator
from typing_extensions import TypedDict, Annotated, List, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
```

#### `ResearcherState` — What each research agent tracks

```python
class ResearcherState(TypedDict):
    """
    State for the research agent containing message history and research metadata.

    This state tracks the researcher's conversation, iteration count for limiting
    tool calls, the research topic being investigated, compressed findings,
    and raw research notes for detailed analysis.
    """
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int
    research_topic: str
    compressed_research: str
    raw_notes: Annotated[List[str], operator.add]
```

| Field | Type | Reducer | Purpose |
|---|---|---|---|
| `researcher_messages` | `Sequence[BaseMessage]` | `add_messages` | The agent's own conversation with the LLM (separate from the supervisor). |
| `tool_call_iterations` | `int` | None (replace) | Counter to limit tool calls and prevent infinite loops. |
| `research_topic` | `str` | None (replace) | The specific sub-topic this agent is researching. |
| `compressed_research` | `str` | None (replace) | Final compressed summary of all findings. |
| `raw_notes` | `List[str]` | `operator.add` | Raw text from tool calls for detailed records. |

**Why separate from AgentState?** Each research agent runs in its own **isolated context window**. It can't see what other agents are doing. It only knows its own `research_topic` and its own `researcher_messages`. This isolation is by design — it prevents agents from being confused by unrelated research.

#### `ResearcherOutputState` — What the research agent returns

```python
class ResearcherOutputState(TypedDict):
    """
    Output state for the research agent containing final research results.

    This represents the final output of the research process with compressed
    research findings and all raw notes from the research process.
    """
    compressed_research: str
    raw_notes: Annotated[List[str], operator.add]
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
```

This is the **output schema** — when the supervisor invokes a research agent, it only gets back these three fields. The `compressed_research` is the key output that the supervisor reads.

#### Additional Pydantic Schemas

```python
class ClarifyWithUser(BaseModel):
    """Schema for user clarification decisions during scoping phase."""
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )

class ResearchQuestion(BaseModel):
    """Schema for research brief generation."""
    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )

class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(description="Important quotes and excerpts from the content")
```

The `Summary` schema is used by `utils.py` to structure webpage summaries. When the Tavily search returns raw HTML content, the summarization model is forced to output a clean `summary` + `key_excerpts` structure.

---

### 3.3 `state_multi_agent_supervisor.py` — Supervisor State

This file defines the **supervisor's state** and the **tools** the supervisor uses to delegate work.

```python
"""
State Definitions for Multi-Agent Research Supervisor

This module defines the state objects and tools used for the multi-agent
research supervisor workflow, including coordination state and research tools.
"""

import operator
from typing_extensions import Annotated, TypedDict, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
```

#### `SupervisorState`

```python
class SupervisorState(TypedDict):
    """
    State for the multi-agent research supervisor.

    Manages coordination between supervisor and research agents, tracking
    research progress and accumulating findings from multiple sub-agents.
    """

    # Messages exchanged with supervisor for coordination and decision-making
    supervisor_messages: Annotated[Sequence[BaseMessage], add_messages]
    # Detailed research brief that guides the overall research direction
    research_brief: str
    # Processed and structured notes ready for final report generation
    notes: Annotated[list[str], operator.add] = []
    # Counter tracking the number of research iterations performed
    research_iterations: int = 0
    # Raw unprocessed research notes collected from sub-agent research
    raw_notes: Annotated[list[str], operator.add] = []
```

| Field | Purpose |
|---|---|
| `supervisor_messages` | The supervisor's conversation with the LLM — includes its decisions and tool results |
| `research_brief` | The research question to investigate (passed in from the scoping phase) |
| `notes` | Compressed research findings from sub-agents (extracted from ToolMessages) |
| `research_iterations` | How many times the supervisor has made decisions — used to enforce a hard limit |
| `raw_notes` | All raw text from sub-agent research for detailed records |

#### Supervisor Tools — `ConductResearch` and `ResearchComplete`

These are **tool-as-schema** definitions. The supervisor LLM can "call" these tools, and the system intercepts them to perform actions.

```python
@tool
class ConductResearch(BaseModel):
    """Tool for delegating a research task to a specialized sub-agent."""
    research_topic: str = Field(
        description="The topic to research. Should be a single topic, and should be described in high detail (at least a paragraph).",
    )
```

When the supervisor LLM calls `ConductResearch(research_topic="...")`, the `supervisor_tools` node intercepts this and:
1. Creates a new `researcher_agent` instance
2. Passes the `research_topic` as input
3. Waits for the agent to finish
4. Returns the compressed research as a `ToolMessage`

```python
@tool
class ResearchComplete(BaseModel):
    """Tool for indicating that the research process is complete."""
    pass
```

When the supervisor calls `ResearchComplete`, it signals that all research is done. The `supervisor_tools` node then ends the graph and returns the aggregated notes.

**How tool calling works under the hood:**

```
Supervisor LLM receives: "Compare React vs Vue vs Svelte..."
         │
         ▼
Supervisor LLM outputs tool calls:
  [
    ConductResearch(research_topic="React for dashboards..."),
    ConductResearch(research_topic="Vue for dashboards..."),
    ConductResearch(research_topic="Svelte for dashboards...")
  ]
         │
         ▼
supervisor_tools node intercepts, launches 3 agents in parallel
         │
         ▼
Each agent returns compressed_research
         │
         ▼
Results packaged as ToolMessages and sent back to supervisor
         │
         ▼
Supervisor LLM sees the results, decides to call ResearchComplete
```

---

## 4. Utilities & Tools

### 4.1 `utils.py` — Search, Summarization & Tools

This is the **toolbox** — contains the Tavily web search integration, content summarization, and the `think_tool`.

```python
"""Research Utilities and Tools.

This module provides search and content processing utilities for the research agent,
including web search capabilities and content summarization tools.
"""

from pathlib import Path
from datetime import datetime
from typing_extensions import Annotated, List, Literal

from langchain.chat_models import init_chat_model 
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from tavily import TavilyClient

from reisearch.state_research import Summary
from reisearch.prompts import summarize_webpage_prompt
```

**Key imports:**
- `TavilyClient` — The Tavily API client for web search. Uses the `TAVILY_API_KEY` env variable.
- `InjectedToolArg` — Marks a parameter as **not visible to the LLM**. The LLM can't set `max_results` or `topic` — they're injected by the system with defaults.
- `Summary` — The Pydantic schema from `state_research.py` used for structured summarization.

#### Helper Functions

```python
def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")
```

Returns something like `"Wed Jun 11, 2025"`. Used in prompts so the LLM knows the current date (important for news/recent events research).

```python
def get_current_dir() -> Path:
    """Get the current directory of the module.

    This function is compatible with Jupyter notebooks and regular Python scripts.

    Returns:
        Path object representing the current directory
    """
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ is not defined
        return Path.cwd()
```

Used by the MCP agent to find the `files/` directory relative to the module. In Jupyter notebooks, `__file__` doesn't exist, so it falls back to `Path.cwd()`.

#### Configuration

```python
summarization_model = init_chat_model(model="openai:gpt-4.1-mini")
tavily_client = TavilyClient()
```

- `summarization_model` — A cheaper, faster model (GPT-4.1-mini) used specifically for summarizing raw webpage content. You don't need a powerful model for this.
- `tavily_client` — Automatically reads `TAVILY_API_KEY` from environment.

#### `tavily_search_multiple` — Batch Web Search

```python
def tavily_search_multiple(
    search_queries: List[str], 
    max_results: int = 3, 
    topic: Literal["general", "news", "finance"] = "general", 
    include_raw_content: bool = True, 
) -> List[dict]:
    """Perform search using Tavily API for multiple queries.

    Args:
        search_queries: List of search queries to execute
        max_results: Maximum number of results per query
        topic: Topic filter for search results
        include_raw_content: Whether to include raw webpage content

    Returns:
        List of search result dictionaries
    """

    # Execute searches sequentially. Note: you can use AsyncTavilyClient to parallelize this step.
    search_docs = []
    for query in search_queries:
        result = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic
        )
        search_docs.append(result)

    return search_docs
```

Takes a list of queries and searches each one sequentially. Each result contains:
- `title` — Page title
- `url` — Page URL  
- `content` — Short snippet
- `raw_content` — Full webpage text (when `include_raw_content=True`)

#### `summarize_webpage_content` — Compress Raw HTML

```python
def summarize_webpage_content(webpage_content: str) -> str:
    """Summarize webpage content using the configured summarization model.

    Args:
        webpage_content: Raw webpage content to summarize

    Returns:
        Formatted summary with key excerpts
    """
    try:
        # Set up structured output model for summarization
        structured_model = summarization_model.with_structured_output(Summary)

        # Generate summary
        summary = structured_model.invoke([
            HumanMessage(content=summarize_webpage_prompt.format(
                webpage_content=webpage_content, 
                date=get_today_str()
            ))
        ])

        # Format summary with clear structure
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )

        return formatted_summary

    except Exception as e:
        print(f"Failed to summarize webpage: {str(e)}")
        return webpage_content[:1000] + "..." if len(webpage_content) > 1000 else webpage_content
```

**What it does:**
1. Takes raw webpage text (could be thousands of lines)
2. Sends it to GPT-4.1-mini with the `summarize_webpage_prompt`
3. Forces structured output using the `Summary` schema
4. Returns a formatted string with `<summary>` and `<key_excerpts>` tags
5. Falls back to truncation if summarization fails

**Why summarize?** Raw webpage content is huge and full of noise (nav bars, footers, ads). Summarization keeps the important facts while fitting within context window limits.

#### `deduplicate_search_results` — Remove Duplicate URLs

```python
def deduplicate_search_results(search_results: List[dict]) -> dict:
    """Deduplicate search results by URL to avoid processing duplicate content.

    Args:
        search_results: List of search result dictionaries

    Returns:
        Dictionary mapping URLs to unique results
    """
    unique_results = {}

    for response in search_results:
        for result in response['results']:
            url = result['url']
            if url not in unique_results:
                unique_results[url] = result

    return unique_results
```

Multiple search queries can return the same webpage. This deduplicates by URL so we don't summarize the same page twice.

#### `process_search_results` — Summarize Each Result

```python
def process_search_results(unique_results: dict) -> dict:
    """Process search results by summarizing content where available.

    Args:
        unique_results: Dictionary of unique search results

    Returns:
        Dictionary of processed results with summaries
    """
    summarized_results = {}

    for url, result in unique_results.items():
        # Use existing content if no raw content for summarization
        if not result.get("raw_content"):
            content = result['content']
        else:
            # Summarize raw content for better processing
            content = summarize_webpage_content(result['raw_content'])

        summarized_results[url] = {
            'title': result['title'],
            'content': content
        }

    return summarized_results
```

For each unique search result:
- If raw content exists → summarize it using the LLM
- If not → use the short snippet from Tavily

#### `format_search_output` — Format for the Agent

```python
def format_search_output(summarized_results: dict) -> str:
    """Format search results into a well-structured string output.

    Args:
        summarized_results: Dictionary of processed search results

    Returns:
        Formatted string of search results with clear source separation
    """
    if not summarized_results:
        return "No valid search results found. Please try different search queries or use a different search API."

    formatted_output = "Search results: \n\n"

    for i, (url, result) in enumerate(summarized_results.items(), 1):
        formatted_output += f"\n\n--- SOURCE {i}: {result['title']} ---\n"
        formatted_output += f"URL: {url}\n\n"
        formatted_output += f"SUMMARY:\n{result['content']}\n\n"
        formatted_output += "-" * 80 + "\n"

    return formatted_output
```

Produces output like:
```
Search results:

--- SOURCE 1: React Dashboard Guide ---
URL: https://example.com/react-dashboards

SUMMARY:
<summary>React is a popular framework for building dashboards...</summary>
<key_excerpts>..."React's virtual DOM makes it ideal for real-time data"...</key_excerpts>

--------------------------------------------------------------------------------
```

#### `tavily_search` — The Main Search Tool

```python
@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 3,
    topic: Annotated[Literal["general", "news", "finance"], InjectedToolArg] = "general",
) -> str:
    """Fetch results from Tavily search API with content summarization.

    Args:
        query: A single search query to execute
        max_results: Maximum number of results to return
        topic: Topic to filter results by ('general', 'news', 'finance')

    Returns:
        Formatted string of search results with summaries
    """
    # Execute search for single query
    search_results = tavily_search_multiple(
        [query],  # Convert single query to list for the internal function
        max_results=max_results,
        topic=topic,
        include_raw_content=True,
    )

    # Deduplicate results by URL to avoid processing duplicate content
    unique_results = deduplicate_search_results(search_results)

    # Process results with summarization
    summarized_results = process_search_results(unique_results)

    # Format output for consumption
    return format_search_output(summarized_results)
```

**This is the tool the LLM actually calls.** Key details:

- `@tool(parse_docstring=True)` — LangChain decorator that converts this function into a tool. The `parse_docstring=True` means the function's docstring is parsed to generate the tool's description and parameter descriptions for the LLM.
- `InjectedToolArg` — The `max_results` and `topic` parameters are **hidden from the LLM**. The LLM only sees and controls the `query` parameter. This prevents the LLM from setting weird values.
- The pipeline: search → deduplicate → summarize → format

#### `think_tool` — Strategic Reflection

```python
@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"
```

**This is a "thinking" tool** — it doesn't actually do anything. It just echoes back the reflection. But it serves a critical purpose:

1. **Forces the LLM to pause and think** — Instead of blindly chaining search after search, the LLM must explicitly reason about what it found and what's missing.
2. **Makes reasoning visible** — The reflection is recorded in the message history, making the agent's decision process transparent.
3. **Improves research quality** — LLMs that reflect between searches produce better research.

---

## 5. Prompt Templates

### 5.1 `prompts.py` — All System Prompts

This file contains **every prompt template** used in the system. Prompts are the instructions that guide the LLMs.

#### `clarify_with_user_instructions` — Scoping Prompt

```python
clarify_with_user_instructions="""
These are the messages that have been exchanged so far from the user asking for the report:
<Messages>
{messages}
</Messages>

Today's date is {date}.

Assess whether you need to ask a clarifying question, or if the user has already provided enough information for you to start research.
IMPORTANT: If you can see in the messages history that you have already asked a clarifying question, you almost always do not need to ask another one. Only ask another question if ABSOLUTELY NECESSARY.

If there are acronyms, abbreviations, or unknown terms, ask the user to clarify.
If you need to ask a question, follow these guidelines:
- Be concise while gathering all necessary information
- Make sure to gather all the information needed to carry out the research task in a concise, well-structured manner.
- Use bullet points or numbered lists if appropriate for clarity. Make sure that this uses markdown formatting and will be rendered correctly if the string output is passed to a markdown renderer.
- Don't ask for unnecessary information, or information that the user has already provided. If you can see that the user has already provided the information, do not ask for it again.

Respond in valid JSON format with these exact keys:
"need_clarification": boolean,
"question": "<question to ask the user to clarify the report scope>",
"verification": "<verification message that we will start research>"

If you need to ask a clarifying question, return:
"need_clarification": true,
"question": "<your clarifying question>",
"verification": ""

If you do not need to ask a clarifying question, return:
"need_clarification": false,
"question": "",
"verification": "<acknowledgement message that you will now start research based on the provided information>"

For the verification message when no clarification is needed:
- Acknowledge that you have sufficient information to proceed
- Briefly summarize the key aspects of what you understand from their request
- Confirm that you will now begin the research process
- Keep the message concise and professional
"""
```

**Purpose:** Decides if the user's question is clear enough. The prompt is designed to avoid over-asking — the "IMPORTANT" note tells it not to keep asking if it already asked once.

#### `transform_messages_into_research_topic_prompt` — Brief Generation

```python
transform_messages_into_research_topic_prompt = """You will be given a set of messages that have been exchanged so far between yourself and the user. 
Your job is to translate these messages into a more detailed and concrete research question that will be used to guide the research.

The messages that have been exchanged so far between yourself and the user are:
<Messages>
{messages}
</Messages>

Today's date is {date}.

You will return a single research question that will be used to guide the research.

Guidelines:
1. Maximize Specificity and Detail
- Include all known user preferences and explicitly list key attributes or dimensions to consider.
- It is important that all details from the user are included in the instructions.

2. Handle Unstated Dimensions Carefully
- When research quality requires considering additional dimensions that the user hasn't specified, acknowledge them as open considerations rather than assumed preferences.
- Example: Instead of assuming "budget-friendly options," say "consider all price ranges unless cost constraints are specified."
- Only mention dimensions that are genuinely necessary for comprehensive research in that domain.

3. Avoid Unwarranted Assumptions
- Never invent specific user preferences, constraints, or requirements that weren't stated.
- If the user hasn't provided a particular detail, explicitly note this lack of specification.
- Guide the researcher to treat unspecified aspects as flexible rather than making assumptions.

4. Distinguish Between Research Scope and User Preferences
- Research scope: What topics/dimensions should be investigated (can be broader than user's explicit mentions)
- User preferences: Specific constraints, requirements, or preferences (must only include what user stated)
- Example: "Research coffee quality factors (including bean sourcing, roasting methods, brewing techniques) for San Francisco coffee shops, with primary focus on taste as specified by the user."

5. Use the First Person
- Phrase the request from the perspective of the user.

6. Sources
- If specific sources should be prioritized, specify them in the research question.
- For product and travel research, prefer linking directly to official or primary websites (e.g., official brand sites, manufacturer pages, or reputable e-commerce platforms like Amazon for user reviews) rather than aggregator sites or SEO-heavy blogs.
- For academic or scientific queries, prefer linking directly to the original paper or official journal publication rather than survey papers or secondary summaries.
- For people, try linking directly to their LinkedIn profile, or their personal website if they have one.
- If the query is in a specific language, prioritize sources published in that language.
"""
```

**Purpose:** Converts a casual user message like "compare react and vue" into a detailed, well-scoped research brief that guides the entire research process. The guidelines prevent the LLM from making assumptions.

#### `research_agent_prompt` — Individual Researcher Instructions

```python
research_agent_prompt =  """You are a research assistant conducting research on the user's input topic. For context, today's date is {date}.

<Task>
Your job is to use tools to gather information about the user's input topic.
You can use any of the tools provided to you to find resources that can help answer the research question. You can call these tools in series or in parallel, your research is conducted in a tool-calling loop.
</Task>

<Available Tools>
You have access to two main tools:
1. **tavily_search**: For conducting web searches to gather information
2. **think_tool**: For reflection and strategic planning during research

**CRITICAL: Use think_tool after each search to reflect on results and plan next steps**
</Available Tools>

<Instructions>
Think like a human researcher with limited time. Follow these steps:

1. **Read the question carefully** - What specific information does the user need?
2. **Start with broader searches** - Use broad, comprehensive queries first
3. **After each search, pause and assess** - Do I have enough to answer? What's still missing?
4. **Execute narrower searches as you gather information** - Fill in the gaps
5. **Stop when you can answer confidently** - Don't keep searching for perfection
</Instructions>

<Hard Limits>
**Tool Call Budgets** (Prevent excessive searching):
- **Simple queries**: Use 2-3 search tool calls maximum
- **Complex queries**: Use up to 5 search tool calls maximum
- **Always stop**: After 5 search tool calls if you cannot find the right sources

**Stop Immediately When**:
- You can answer the user's question comprehensively
- You have 3+ relevant examples/sources for the question
- Your last 2 searches returned similar information
</Hard Limits>

<Show Your Thinking>
After each search tool call, use think_tool to analyze the results:
- What key information did I find?
- What's missing?
- Do I have enough to answer the question comprehensively?
- Should I search more or provide my answer?
</Show Your Thinking>
"""
```

**Purpose:** Instructions for each individual researcher agent. Key design decisions:
- **Hard limits on tool calls** — Prevents the agent from searching forever (max 5 searches)
- **Think-after-search pattern** — Forces reflection between searches
- **Broad-to-narrow strategy** — Start wide, then focus

#### `research_agent_prompt_with_mcp` — MCP Variant Instructions

```python
research_agent_prompt_with_mcp = """You are a research assistant conducting research on the user's input topic using local files. For context, today's date is {date}.

<Task>
Your job is to use file system tools to gather information from local research files.
You can use any of the tools provided to you to find and read files that help answer the research question. You can call these tools in series or in parallel, your research is conducted in a tool-calling loop.
</Task>

<Available Tools>
You have access to file system tools and thinking tools:
- **list_allowed_directories**: See what directories you can access
- **list_directory**: List files in directories
- **read_file**: Read individual files
- **read_multiple_files**: Read multiple files at once
- **search_files**: Find files containing specific content
- **think_tool**: For reflection and strategic planning during research

**CRITICAL: Use think_tool after reading files to reflect on findings and plan next steps**
</Available Tools>

<Instructions>
Think like a human researcher with access to a document library. Follow these steps:

1. **Read the question carefully** - What specific information does the user need?
2. **Explore available files** - Use list_allowed_directories and list_directory to understand what's available
3. **Identify relevant files** - Use search_files if needed to find documents matching the topic
4. **Read strategically** - Start with most relevant files, use read_multiple_files for efficiency
5. **After reading, pause and assess** - Do I have enough to answer? What's still missing?
6. **Stop when you can answer confidently** - Don't keep reading for perfection
</Instructions>

<Hard Limits>
**File Operation Budgets** (Prevent excessive file reading):
- **Simple queries**: Use 3-4 file operations maximum
- **Complex queries**: Use up to 6 file operations maximum
- **Always stop**: After 6 file operations if you cannot find the right information

**Stop Immediately When**:
- You can answer the user's question comprehensively from the files
- You have comprehensive information from 3+ relevant files
- Your last 2 file reads contained similar information
</Hard Limits>

<Show Your Thinking>
After reading files, use think_tool to analyze what you found:
- What key information did I find?
- What's missing?
- Do I have enough to answer the question comprehensively?
- Should I read more files or provide my answer?
- Always cite which files you used for your information
</Show Your Thinking>"""
```

**Purpose:** Same structure as the web search prompt, but adapted for file system operations via MCP.

#### `lead_researcher_prompt` — Supervisor Instructions

```python
lead_researcher_prompt = """You are a research supervisor. Your job is to conduct research by calling the "ConductResearch" tool. For context, today's date is {date}.

<Task>
Your focus is to call the "ConductResearch" tool to conduct research against the overall research question passed in by the user. 
When you are completely satisfied with the research findings returned from the tool calls, then you should call the "ResearchComplete" tool to indicate that you are done with your research.
</Task>

<Available Tools>
You have access to three main tools:
1. **ConductResearch**: Delegate research tasks to specialized sub-agents
2. **ResearchComplete**: Indicate that research is complete
3. **think_tool**: For reflection and strategic planning during research

**CRITICAL: Use think_tool before calling ConductResearch to plan your approach, and after each ConductResearch to assess progress**
**PARALLEL RESEARCH**: When you identify multiple independent sub-topics that can be explored simultaneously, make multiple ConductResearch tool calls in a single response to enable parallel research execution. This is more efficient than sequential research for comparative or multi-faceted questions. Use at most {max_concurrent_research_units} parallel agents per iteration.
</Available Tools>

<Instructions>
Think like a research manager with limited time and resources. Follow these steps:

1. **Read the question carefully** - What specific information does the user need?
2. **Decide how to delegate the research** - Carefully consider the question and decide how to delegate the research. Are there multiple independent directions that can be explored simultaneously?
3. **After each call to ConductResearch, pause and assess** - Do I have enough to answer? What's still missing?
</Instructions>

<Hard Limits>
**Task Delegation Budgets** (Prevent excessive delegation):
- **Bias towards single agent** - Use single agent for simplicity unless the user request has clear opportunity for parallelization
- **Stop when you can answer confidently** - Don't keep delegating research for perfection
- **Limit tool calls** - Always stop after {max_researcher_iterations} tool calls to think_tool and ConductResearch if you cannot find the right sources
</Hard Limits>

<Show Your Thinking>
Before you call ConductResearch tool call, use think_tool to plan your approach:
- Can the task be broken down into smaller sub-tasks?

After each ConductResearch tool call, use think_tool to analyze the results:
- What key information did I find?
- What's missing?
- Do I have enough to answer the question comprehensively?
- Should I delegate more research or call ResearchComplete?
</Show Your Thinking>

<Scaling Rules>
**Simple fact-finding, lists, and rankings** can use a single sub-agent:
- *Example*: List the top 10 coffee shops in San Francisco → Use 1 sub-agent

**Comparisons presented in the user request** can use a sub-agent for each element of the comparison:
- *Example*: Compare OpenAI vs. Anthropic vs. DeepMind approaches to AI safety → Use 3 sub-agents
- Delegate clear, distinct, non-overlapping subtopics

**Important Reminders:**
- Each ConductResearch call spawns a dedicated research agent for that specific topic
- A separate agent will write the final report - you just need to gather information
- When calling ConductResearch, provide complete standalone instructions - sub-agents can't see other agents' work
- Do NOT use acronyms or abbreviations in your research questions, be very clear and specific
</Scaling Rules>"""
```

**Purpose:** The supervisor's brain. Key design patterns:
- **Parallel research** — It can call `ConductResearch` multiple times in one turn to launch parallel agents
- **Scaling rules** — Simple questions get 1 agent, comparisons get N agents
- **Standalone instructions** — Each sub-agent is isolated, so the supervisor must give complete context

#### `compress_research_system_prompt` — Research Compression

```python
compress_research_system_prompt = """You are a research assistant that has conducted research on a topic by calling several tools and web searches. Your job is now to clean up the findings, but preserve all of the relevant statements and information that the researcher has gathered. For context, today's date is {date}.

<Task>
You need to clean up information gathered from tool calls and web searches in the existing messages.
All relevant information should be repeated and rewritten verbatim, but in a cleaner format.
The purpose of this step is just to remove any obviously irrelevant or duplicate information.
For example, if three sources all say "X", you could say "These three sources all stated X".
Only these fully comprehensive cleaned findings are going to be returned to the user, so it's crucial that you don't lose any information from the raw messages.
</Task>

<Tool Call Filtering>
**IMPORTANT**: When processing the research messages, focus only on substantive research content:
- **Include**: All tavily_search results and findings from web searches
- **Exclude**: think_tool calls and responses - these are internal agent reflections for decision-making and should not be included in the final research report
- **Focus on**: Actual information gathered from external sources, not the agent's internal reasoning process

The think_tool calls contain strategic reflections and decision-making notes that are internal to the research process but do not contain factual information that should be preserved in the final report.
</Tool Call Filtering>

<Guidelines>
1. Your output findings should be fully comprehensive and include ALL of the information and sources that the researcher has gathered from tool calls and web searches. It is expected that you repeat key information verbatim.
2. This report can be as long as necessary to return ALL of the information that the researcher has gathered.
3. In your report, you should return inline citations for each source that the researcher found.
4. You should include a "Sources" section at the end of the report that lists all of the sources the researcher found with corresponding citations, cited against statements in the report.
5. Make sure to include ALL of the sources that the researcher gathered in the report, and how they were used to answer the question!
6. It's really important not to lose any sources. A later LLM will be used to merge this report with others, so having all of the sources is critical.
</Guidelines>

<Output Format>
The report should be structured like this:
**List of Queries and Tool Calls Made**
**Fully Comprehensive Findings**
**List of All Relevant Sources (with citations in the report)**
</Output Format>

<Citation Rules>
- Assign each unique URL a single citation number in your text
- End with ### Sources that lists each source with corresponding numbers
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list regardless of which sources you choose
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
</Citation Rules>

Critical Reminder: It is extremely important that any information that is even remotely relevant to the user's research topic is preserved verbatim (e.g. don't rewrite it, don't summarize it, don't paraphrase it).
"""
```

**Purpose:** After a research agent finishes searching, this prompt takes all the raw messages (search results, tool calls, AI responses) and compresses them into a clean, source-cited summary. It's designed to **preserve everything** — better to be too comprehensive than to lose information.

#### `compress_research_human_message` — Compression Trigger

```python
compress_research_human_message = """All above messages are about research conducted by an AI Researcher for the following research topic:

RESEARCH TOPIC: {research_topic}

Your task is to clean up these research findings while preserving ALL information that is relevant to answering this specific research question. 

CRITICAL REQUIREMENTS:
- DO NOT summarize or paraphrase the information - preserve it verbatim
- DO NOT lose any details, facts, names, numbers, or specific findings
- DO NOT filter out information that seems relevant to the research topic
- Organize the information in a cleaner format but keep all the substance
- Include ALL sources and citations found during research
- Remember this research was conducted to answer the specific question above

The cleaned findings will be used for final report generation, so comprehensiveness is critical."""
```

**Purpose:** This is appended as the final human message when compressing research. It reminds the LLM of the research topic and emphasizes preserving ALL information.

#### `final_report_generation_prompt` — Report Writing

```python
final_report_generation_prompt = """Based on all the research conducted, create a comprehensive, well-structured answer to the overall research brief:
<Research Brief>
{research_brief}
</Research Brief>

CRITICAL: Make sure the answer is written in the same language as the human messages!
For example, if the user's messages are in English, then MAKE SURE you write your response in English. If the user's messages are in Chinese, then MAKE SURE you write your entire response in Chinese.
This is critical. The user will only understand the answer if it is written in the same language as their input message.

Today's date is {date}.

Here are the findings from the research that you conducted:
<Findings>
{findings}
</Findings>

Please create a detailed answer to the overall research brief that:
1. Is well-organized with proper headings (# for title, ## for sections, ### for subsections)
2. Includes specific facts and insights from the research
3. References relevant sources using [Title](URL) format
4. Provides a balanced, thorough analysis. Be as comprehensive as possible, and include all information that is relevant to the overall research question. People are using you for deep research and will expect detailed, comprehensive answers.
5. Includes a "Sources" section at the end with all referenced links

You can structure your report in a number of different ways. Here are some examples:

To answer a question that asks you to compare two things, you might structure your report like this:
1/ intro
2/ overview of topic A
3/ overview of topic B
4/ comparison between A and B
5/ conclusion

To answer a question that asks you to return a list of things, you might only need a single section which is the entire list.
1/ list of things or table of things
Or, you could choose to make each item in the list a separate section in the report. When asked for lists, you don't need an introduction or conclusion.
1/ item 1
2/ item 2
3/ item 3

To answer a question that asks you to summarize a topic, give a report, or give an overview, you might structure your report like this:
1/ overview of topic
2/ concept 1
3/ concept 2
4/ concept 3
5/ conclusion

If you think you can answer the question with a single section, you can do that too!
1/ answer

REMEMBER: Section is a VERY fluid and loose concept. You can structure your report however you think is best, including in ways that are not listed above!
Make sure that your sections are cohesive, and make sense for the reader.

For each section of the report, do the following:
- Use simple, clear language
- Use ## for section title (Markdown format) for each section of the report
- Do NOT ever refer to yourself as the writer of the report. This should be a professional report without any self-referential language. 
- Do not say what you are doing in the report. Just write the report without any commentary from yourself.
- Each section should be as long as necessary to deeply answer the question with the information you have gathered. It is expected that sections will be fairly long and verbose. You are writing a deep research report, and users will expect a thorough answer.
- Use bullet points to list out information when appropriate, but by default, write in paragraph form.

REMEMBER:
The brief and research may be in English, but you need to translate this information to the right language when writing the final answer.
Make sure the final answer report is in the SAME language as the human messages in the message history.

Format the report in clear markdown with proper structure and include source references where appropriate.

<Citation Rules>
- Assign each unique URL a single citation number in your text
- End with ### Sources that lists each source with corresponding numbers
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list regardless of which sources you choose
- Each source should be a separate line item in a list, so that in markdown it is rendered as a list.
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
- Citations are extremely important. Make sure to include these, and pay a lot of attention to getting these right. Users will often use these citations to look into more information.
</Citation Rules>
"""
```

**Purpose:** The final step — takes all compressed research findings and writes a polished, well-structured markdown report. Supports multilingual output (matches the user's language).

#### Evaluation Prompts (for testing quality)

```python
BRIEF_CRITERIA_PROMPT = """
<role>
You are an expert research brief evaluator specializing in assessing whether generated research briefs accurately capture user-specified criteria without loss of important details.
</role>

<task>
Determine if the research brief adequately captures the specific success criterion provided. Return a binary assessment with detailed reasoning.
</task>

<evaluation_context>
Research briefs are critical for guiding downstream research agents. Missing or inadequately captured criteria can lead to incomplete research that fails to address user needs. Accurate evaluation ensures research quality and user satisfaction.
</evaluation_context>

<criterion_to_evaluate>
{criterion}
</criterion_to_evaluate>

<research_brief>
{research_brief}
</research_brief>

<evaluation_guidelines>
CAPTURED (criterion is adequately represented) if:
- The research brief explicitly mentions or directly addresses the criterion
- The brief contains equivalent language or concepts that clearly cover the criterion
- The criterion's intent is preserved even if worded differently
- All key aspects of the criterion are represented in the brief

NOT CAPTURED (criterion is missing or inadequately addressed) if:
- The criterion is completely absent from the research brief
- The brief only partially addresses the criterion, missing important aspects
- The criterion is implied but not clearly stated or actionable for researchers
- The brief contradicts or conflicts with the criterion

<evaluation_examples>
Example 1 - CAPTURED:
Criterion: "Current age is 25"
Brief: "...investment advice for a 25-year-old investor..."
Judgment: CAPTURED - age is explicitly mentioned

Example 2 - NOT CAPTURED:
Criterion: "Monthly rent below 7k"
Brief: "...find apartments in Manhattan with good amenities..."
Judgment: NOT CAPTURED - budget constraint is completely missing

Example 3 - CAPTURED:
Criterion: "High risk tolerance"
Brief: "...willing to accept significant market volatility for higher returns..."
Judgment: CAPTURED - equivalent concept expressed differently

Example 4 - NOT CAPTURED:
Criterion: "Doorman building required"
Brief: "...find apartments with modern amenities..."
Judgment: NOT CAPTURED - specific doorman requirement not mentioned
</evaluation_examples>
</evaluation_guidelines>

<output_instructions>
1. Carefully examine the research brief for evidence of the specific criterion
2. Look for both explicit mentions and equivalent concepts
3. Provide specific quotes or references from the brief as evidence
4. Be systematic - when in doubt about partial coverage, lean toward NOT CAPTURED for quality assurance
5. Focus on whether a researcher could act on this criterion based on the brief alone
</output_instructions>"""
```

```python
BRIEF_HALLUCINATION_PROMPT = """
## Brief Hallucination Evaluator

<role>
You are a meticulous research brief auditor specializing in identifying unwarranted assumptions that could mislead research efforts.
</role>

<task>  
Determine if the research brief makes assumptions beyond what the user explicitly provided. Return a binary pass/fail judgment.
</task>

<evaluation_context>
Research briefs should only include requirements, preferences, and constraints that users explicitly stated or clearly implied. Adding assumptions can lead to research that misses the user's actual needs.
</evaluation_context>

<research_brief>
{research_brief}
</research_brief>

<success_criteria>
{success_criteria}
</success_criteria>

<evaluation_guidelines>
PASS (no unwarranted assumptions) if:
- Brief only includes explicitly stated user requirements
- Any inferences are clearly marked as such or logically necessary
- Source suggestions are general recommendations, not specific assumptions
- Brief stays within the scope of what the user actually requested

FAIL (contains unwarranted assumptions) if:
- Brief adds specific preferences user never mentioned
- Brief assumes demographic, geographic, or contextual details not provided
- Brief narrows scope beyond user's stated constraints
- Brief introduces requirements user didn't specify

<evaluation_examples>
Example 1 - PASS:
User criteria: ["Looking for coffee shops", "In San Francisco"] 
Brief: "...research coffee shops in San Francisco area..."
Judgment: PASS - stays within stated scope

Example 2 - FAIL:
User criteria: ["Looking for coffee shops", "In San Francisco"]
Brief: "...research trendy coffee shops for young professionals in San Francisco..."
Judgment: FAIL - assumes "trendy" and "young professionals" demographics

Example 3 - PASS:
User criteria: ["Budget under $3000", "2 bedroom apartment"]
Brief: "...find 2-bedroom apartments within $3000 budget, consulting rental sites and local listings..."
Judgment: PASS - source suggestions are appropriate, no preference assumptions

Example 4 - FAIL:
User criteria: ["Budget under $3000", "2 bedroom apartment"] 
Brief: "...find modern 2-bedroom apartments under $3000 in safe neighborhoods with good schools..."
Judgment: FAIL - assumes "modern", "safe", and "good schools" preferences
</evaluation_examples>
</evaluation_guidelines>

<output_instructions>
Carefully scan the brief for any details not explicitly provided by the user. Be strict - when in doubt about whether something was user-specified, lean toward FAIL.
</output_instructions>"""
```

**Purpose:** These two prompts are for **automated quality evaluation** of research briefs:
- `BRIEF_CRITERIA_PROMPT` — Checks if the brief captured all user requirements
- `BRIEF_HALLUCINATION_PROMPT` — Checks if the brief added assumptions the user didn't state

#### `summarize_webpage_prompt` — Webpage Summarization

```python
summarize_webpage_prompt = """You are tasked with summarizing the raw content of a webpage retrieved from a web search. Your goal is to create a summary that preserves the most important information from the original web page. This summary will be used by a downstream research agent, so it's crucial to maintain the key details without losing essential information.

Here is the raw content of the webpage:

<webpage_content>
{webpage_content}
</webpage_content>

Please follow these guidelines to create your summary:

1. Identify and preserve the main topic or purpose of the webpage.
2. Retain key facts, statistics, and data points that are central to the content's message.
3. Keep important quotes from credible sources or experts.
4. Maintain the chronological order of events if the content is time-sensitive or historical.
5. Preserve any lists or step-by-step instructions if present.
6. Include relevant dates, names, and locations that are crucial to understanding the content.
7. Summarize lengthy explanations while keeping the core message intact.

When handling different types of content:

- For news articles: Focus on the who, what, when, where, why, and how.
- For scientific content: Preserve methodology, results, and conclusions.
- For opinion pieces: Maintain the main arguments and supporting points.
- For product pages: Keep key features, specifications, and unique selling points.

Your summary should be significantly shorter than the original content but comprehensive enough to stand alone as a source of information. Aim for about 25-30 percent of the original length, unless the content is already concise.

Present your summary in the following format:

```
{{
   "summary": "Your summary here, structured with appropriate paragraphs or bullet points as needed",
   "key_excerpts": "First important quote or excerpt, Second important quote or excerpt, Third important quote or excerpt, ...Add more excerpts as needed, up to a maximum of 5"
}}
```

Here are two examples of good summaries:

Example 1 (for a news article):
```json
{{
   "summary": "On July 15, 2023, NASA successfully launched the Artemis II mission from Kennedy Space Center. This marks the first crewed mission to the Moon since Apollo 17 in 1972. The four-person crew, led by Commander Jane Smith, will orbit the Moon for 10 days before returning to Earth. This mission is a crucial step in NASA's plans to establish a permanent human presence on the Moon by 2030.",
   "key_excerpts": "Artemis II represents a new era in space exploration, said NASA Administrator John Doe. The mission will test critical systems for future long-duration stays on the Moon, explained Lead Engineer Sarah Johnson. We're not just going back to the Moon, we're going forward to the Moon, Commander Jane Smith stated during the pre-launch press conference."
}}
```

Example 2 (for a scientific article):
```json
{{
   "summary": "A new study published in Nature Climate Change reveals that global sea levels are rising faster than previously thought. Researchers analyzed satellite data from 1993 to 2022 and found that the rate of sea-level rise has accelerated by 0.08 mm/year² over the past three decades. This acceleration is primarily attributed to melting ice sheets in Greenland and Antarctica. The study projects that if current trends continue, global sea levels could rise by up to 2 meters by 2100, posing significant risks to coastal communities worldwide.",
   "key_excerpts": "Our findings indicate a clear acceleration in sea-level rise, which has significant implications for coastal planning and adaptation strategies, lead author Dr. Emily Brown stated. The rate of ice sheet melt in Greenland and Antarctica has tripled since the 1990s, the study reports. Without immediate and substantial reductions in greenhouse gas emissions, we are looking at potentially catastrophic sea-level rise by the end of this century, warned co-author Professor Michael Green."  
}}
```

Remember, your goal is to create a summary that can be easily understood and utilized by a downstream research agent while preserving the most critical information from the original webpage.

Today's date is {date}.
"""
```

**Purpose:** Tells the summarization model exactly how to compress a raw webpage. The examples help the LLM understand the expected format. The structured output (via `Summary` Pydantic schema) ensures consistent output.

---

## 6. Research Agent (Single Agent)

### 6.1 `research_agent.py` — Web Search Agent

This is the **worker agent** — a single researcher that searches the web and compresses its findings.

```python
"""Research Agent Implementation.

This module implements a research agent that can perform iterative web searches
and synthesis to answer complex research questions.
"""

from pydantic import BaseModel, Field
from typing_extensions import Literal

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from langchain.chat_models import init_chat_model

from reisearch.state_research import ResearcherState, ResearcherOutputState
from reisearch.utils import tavily_search, get_today_str, think_tool
from reisearch.prompts import research_agent_prompt, compress_research_system_prompt, compress_research_human_message
```

#### Configuration

```python
# Set up tools and model binding
tools = [tavily_search, think_tool]
tools_by_name = {tool.name: tool for tool in tools}

# Initialize models
model = init_chat_model(model="anthropic:claude-sonnet-4-20250514")
model_with_tools = model.bind_tools(tools)
summarization_model = init_chat_model(model="openai:gpt-4.1-mini")
compress_model = init_chat_model(model="openai:gpt-4.1", max_tokens=32000)
```

**Models used:**
| Model | Role | Why this model? |
|---|---|---|
| Claude Sonnet 4 | Main researcher LLM | Excellent at tool calling and reasoning |
| GPT-4.1-mini | Webpage summarization | Cheap and fast for simple summarization |
| GPT-4.1 | Research compression | Good at long-form synthesis with 32k output |

`model.bind_tools(tools)` tells the LLM about the available tools. After binding, the LLM can output tool calls in its responses.

#### Node: `llm_call` — The Research Brain

```python
def llm_call(state: ResearcherState):
    """Analyze current state and decide on next actions.

    The model analyzes the current conversation state and decides whether to:
    1. Call search tools to gather more information
    2. Provide a final answer based on gathered information

    Returns updated state with the model's response.
    """
    return {
        "researcher_messages": [
            model_with_tools.invoke(
                [SystemMessage(content=research_agent_prompt)] + state["researcher_messages"]
            )
        ]
    }
```

**What happens here:**
1. Takes the system prompt (`research_agent_prompt`) + all previous messages
2. Sends them to Claude Sonnet 4 with tools bound
3. The LLM either:
   - Returns tool calls (e.g., `tavily_search(query="React dashboard performance")`)
   - Returns a text response (when it's done searching)
4. The response is appended to `researcher_messages`

**Note:** The system prompt doesn't use `{date}` formatting here — it's injected as-is. This means the date formatting happens at import time, not at runtime. (This is a minor bug in the original code — it should use `.format(date=get_today_str())`.)

#### Node: `tool_node` — Execute Tool Calls

```python
def tool_node(state: ResearcherState):
    """Execute all tool calls from the previous LLM response.

    Executes all tool calls from the previous LLM responses.
    Returns updated state with tool execution results.
    """
    tool_calls = state["researcher_messages"][-1].tool_calls

    # Execute all tool calls
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observations.append(tool.invoke(tool_call["args"]))

    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]

    return {"researcher_messages": tool_outputs}
```

**Step by step:**
1. Gets the last AI message's tool calls (could be 1 or more)
2. Looks up each tool by name in `tools_by_name` dictionary
3. Invokes each tool with the arguments the LLM provided
4. Wraps each result in a `ToolMessage` with the matching `tool_call_id`
5. Returns the tool messages — they get appended to `researcher_messages`

**Why `tool_call_id`?** LLMs need to see which tool result corresponds to which tool call. The `tool_call_id` links them together. Without it, the LLM would be confused about which result goes with which request.

#### Node: `compress_research` — Summarize Findings

```python
def compress_research(state: ResearcherState) -> dict:
    """Compress research findings into a concise summary.

    Takes all the research messages and tool outputs and creates
    a compressed summary suitable for the supervisor's decision-making.
    """

    system_message = compress_research_system_prompt.format(date=get_today_str())
    messages = [SystemMessage(content=system_message)] + state.get("researcher_messages", []) + [HumanMessage(content=compress_research_human_message)]
    response = compress_model.invoke(messages)

    # Extract raw notes from tool and AI messages
    raw_notes = [
        str(m.content) for m in filter_messages(
            state["researcher_messages"], 
            include_types=["tool", "ai"]
        )
    ]

    return {
        "compressed_research": str(response.content),
        "raw_notes": ["\n".join(raw_notes)]
    }
```

**What happens:**
1. Builds a message list: system prompt → all research messages → human trigger message
2. Sends to GPT-4.1 (the compression model)
3. GPT-4.1 reads all the search results and tool responses, and produces a clean, cited summary
4. Also extracts raw notes from all tool and AI messages for record-keeping
5. Returns both `compressed_research` (clean) and `raw_notes` (raw)

#### Routing: `should_continue`

```python
def should_continue(state: ResearcherState) -> Literal["tool_node", "compress_research"]:
    """Determine whether to continue research or provide final answer.

    Determines whether the agent should continue the research loop or provide
    a final answer based on whether the LLM made tool calls.

    Returns:
        "tool_node": Continue to tool execution
        "compress_research": Stop and compress research
    """
    messages = state["researcher_messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, continue to tool execution
    if last_message.tool_calls:
        return "tool_node"
    # Otherwise, we have a final answer
    return "compress_research"
```

**Simple routing logic:**
- If the LLM's last message has tool calls → go to `tool_node` (execute them)
- If not → the LLM decided it's done → go to `compress_research`

#### Graph Construction

```python
# Build the agent workflow
agent_builder = StateGraph(ResearcherState, output_schema=ResearcherOutputState)

# Add nodes to the graph
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("compress_research", compress_research)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",        # Continue research loop
        "compress_research": "compress_research",  # Provide final answer
    },
)
agent_builder.add_edge("tool_node", "llm_call")  # Loop back for more research
agent_builder.add_edge("compress_research", END)

# Compile the agent
researcher_agent = agent_builder.compile()
```

**The graph looks like this:**

```
START
  │
  ▼
llm_call ◄──────────────────────┐
  │                              │
  ├── has tool calls? ──▶ tool_node
  │                       (execute tools, loop back)
  │
  └── no tool calls? ──▶ compress_research
                              │
                              ▼
                             END
```

Key points:
- `output_schema=ResearcherOutputState` — Only `compressed_research`, `raw_notes`, and `researcher_messages` are returned to the caller
- The `tool_node → llm_call` loop continues until the LLM stops making tool calls
- `compress_research` is always the final step before END

---

## 7. Research Agent MCP (File-Based Variant)

### 7.1 `research_agent_mcp.py` — MCP Agent

This is an **alternative version** of the research agent that reads local files instead of searching the web. It uses the **Model Context Protocol (MCP)** to access a filesystem server.

```python
"""Research Agent with MCP Integration.

This module implements a research agent that integrates with Model Context Protocol (MCP)
servers to access tools and resources. The agent demonstrates how to use MCP filesystem
server for local document research and analysis.

Key features:
- MCP server integration for tool access
- Async operations for concurrent tool execution (required by MCP protocol)
- Filesystem operations for local document research
- Secure directory access with permission checking
- Research compression for efficient processing
- Lazy MCP client initialization for LangGraph Platform compatibility
"""

import os

from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, START, END

from reisearch.prompts import research_agent_prompt_with_mcp, compress_research_system_prompt, compress_research_human_message
from reisearch.state_research import ResearcherState, ResearcherOutputState
from reisearch.utils import get_today_str, think_tool, get_current_dir
```

#### MCP Configuration

```python
# MCP server configuration for filesystem access
mcp_config = {
    "filesystem": {
        "command": "npx",
        "args": [
            "-y",  # Auto-install if needed
            "@modelcontextprotocol/server-filesystem",
            str(get_current_dir() / "files")  # Path to research documents
        ],
        "transport": "stdio"  # Communication via stdin/stdout
    }
}
```

**What is MCP?** The Model Context Protocol is a standard for LLMs to interact with external tools and data sources. Here, it launches a filesystem server as a subprocess. The server exposes tools like `read_file`, `list_directory`, `search_files`, etc.

**How it works:**
1. `npx` runs the `@modelcontextprotocol/server-filesystem` package
2. The server gets access to the `files/` directory
3. It communicates with the Python process via stdin/stdout (stdio transport)
4. The LLM can call filesystem tools through this server

#### Lazy Client Initialization

```python
# Global client variable - will be initialized lazily
_client = None

def get_mcp_client():
    """Get or initialize MCP client lazily to avoid issues with LangGraph Platform."""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(mcp_config)
    return _client
```

**Why lazy?** On LangGraph Platform (cloud deployment), the module gets imported at startup. If the MCP client is created at import time, it would fail because the subprocess can't be started during module loading. Lazy initialization defers creation until the first actual use.

#### Configuration

```python
compress_model = init_chat_model(model="openai:gpt-4.1", max_tokens=32000)
model = init_chat_model(model="anthropic:claude-sonnet-4-20250514")
```

#### Node: `llm_call` (async)

```python
async def llm_call(state: ResearcherState):
    """Analyze current state and decide on tool usage with MCP integration.

    This node:
    1. Retrieves available tools from MCP server
    2. Binds tools to the language model
    3. Processes user input and decides on tool usage

    Returns updated state with model response.
    """
    # Get available tools from MCP server
    client = get_mcp_client()
    mcp_tools = await client.get_tools()

    # Use MCP tools for local document access
    tools = mcp_tools + [think_tool]

    # Initialize model with tool binding
    model_with_tools = model.bind_tools(tools)

    # Process user input with system prompt
    return {
        "researcher_messages": [
            model_with_tools.invoke(
                [SystemMessage(content=research_agent_prompt_with_mcp.format(date=get_today_str()))] + state["researcher_messages"]
            )
        ]
    }
```

**Key difference from web version:** Tools are fetched dynamically from the MCP server at each call (`await client.get_tools()`), rather than being hardcoded. This means the available tools can change if the MCP server adds/removes capabilities.

#### Node: `tool_node` (async)

```python
async def tool_node(state: ResearcherState):
    """Execute tool calls using MCP tools.

    This node:
    1. Retrieves current tool calls from the last message
    2. Executes all tool calls using async operations (required for MCP)
    3. Returns formatted tool results

    Note: MCP requires async operations due to inter-process communication
    with the MCP server subprocess. This is unavoidable.
    """
    tool_calls = state["researcher_messages"][-1].tool_calls

    async def execute_tools():
        """Execute all tool calls. MCP tools require async execution."""
        # Get fresh tool references from MCP server
        client = get_mcp_client()
        mcp_tools = await client.get_tools()
        tools = mcp_tools + [think_tool]
        tools_by_name = {tool.name: tool for tool in tools}

        # Execute tool calls (sequentially for reliability)
        observations = []
        for tool_call in tool_calls:
            tool = tools_by_name[tool_call["name"]]
            if tool_call["name"] == "think_tool":
                # think_tool is sync, use regular invoke
                observation = tool.invoke(tool_call["args"])
            else:
                # MCP tools are async, use ainvoke
                observation = await tool.ainvoke(tool_call["args"])
            observations.append(observation)

        # Format results as tool messages
        tool_outputs = [
            ToolMessage(
                content=observation,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
            for observation, tool_call in zip(observations, tool_calls)
        ]

        return tool_outputs

    messages = await execute_tools()

    return {"researcher_messages": messages}
```

**Key differences:**
- All MCP tool calls use `ainvoke` (async) because they communicate with the MCP subprocess
- `think_tool` is a regular Python function, so it uses sync `invoke`
- Tools are re-fetched from the MCP server each time (in case they changed)

#### Node: `compress_research` (same as web version)

```python
def compress_research(state: ResearcherState) -> dict:
    """Compress research findings into a concise summary.

    Takes all the research messages and tool outputs and creates
    a compressed summary suitable for further processing or reporting.

    This function filters out think_tool calls and focuses on substantive
    file-based research content from MCP tools.
    """

    system_message = compress_research_system_prompt.format(date=get_today_str())
    messages = [SystemMessage(content=system_message)] + state.get("researcher_messages", []) + [HumanMessage(content=compress_research_human_message)]

    response = compress_model.invoke(messages)

    # Extract raw notes from tool and AI messages
    raw_notes = [
        str(m.content) for m in filter_messages(
            state["researcher_messages"], 
            include_types=["tool", "ai"]
        )
    ]

    return {
        "compressed_research": str(response.content),
        "raw_notes": ["\n".join(raw_notes)]
    }
```

#### Routing & Graph Construction

```python
def should_continue(state: ResearcherState) -> Literal["tool_node", "compress_research"]:
    """Determine whether to continue with tool execution or compress research."""
    messages = state["researcher_messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"
    return "compress_research"

# Build the agent workflow
agent_builder_mcp = StateGraph(ResearcherState, output_schema=ResearcherOutputState)

agent_builder_mcp.add_node("llm_call", llm_call)
agent_builder_mcp.add_node("tool_node", tool_node)
agent_builder_mcp.add_node("compress_research", compress_research)

agent_builder_mcp.add_edge(START, "llm_call")
agent_builder_mcp.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "compress_research": "compress_research",
    },
)
agent_builder_mcp.add_edge("tool_node", "llm_call")
agent_builder_mcp.add_edge("compress_research", END)

# Compile the agent
agent_mcp = agent_builder_mcp.compile()
```

Same graph structure as the web version, just using MCP tools instead of Tavily.

---

## 8. Research Scoping Agent

### 8.1 `research_agent_scope.py` — Clarify & Brief

This module handles the **first two steps** of the pipeline: determining if the user's question is clear enough, and generating a detailed research brief.

```python
"""User Clarification and Research Brief Generation.

This module implements the scoping phase of the research workflow, where we:
1. Assess if the user's request needs clarification
2. Generate a detailed research brief from the conversation

The workflow uses structured output to make deterministic decisions about
whether sufficient context exists to proceed with research.
"""

from datetime import datetime
from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, get_buffer_string
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from reisearch.prompts import clarify_with_user_instructions, transform_messages_into_research_topic_prompt
from reisearch.state_scope import AgentState, ClarifyWithUser, ResearchQuestion, AgentInputState
```

**New imports:**
- `get_buffer_string` — Converts a list of `BaseMessage` objects into a human-readable string (like a chat transcript)
- `Command` — A LangGraph object that lets a node both update state AND choose the next node to go to. More flexible than regular return values.

#### Configuration

```python
def get_today_str() -> str:
    """Get current date in a human-readable format."""
    return datetime.now().strftime("%a %b %-d, %Y")

# Initialize model
model = init_chat_model(model="openai:gpt-4.1", temperature=0.0)
```

Uses GPT-4.1 with `temperature=0.0` for deterministic, consistent outputs. The scoping step needs to be reliable, not creative.

#### Node: `clarify_with_user` — Decide if clarification is needed

```python
def clarify_with_user(state: AgentState) -> Command[Literal["write_research_brief", "__end__"]]:
    """
    Determine if the user's request contains sufficient information to proceed with research.

    Uses structured output to make deterministic decisions and avoid hallucination.
    Routes to either research brief generation or ends with a clarification question.
    """
    # Set up structured output model
    structured_output_model = model.with_structured_output(ClarifyWithUser)

    # Invoke the model with clarification instructions
    response = structured_output_model.invoke([
        HumanMessage(content=clarify_with_user_instructions.format(
            messages=get_buffer_string(messages=state["messages"]), 
            date=get_today_str()
        ))
    ])

    # Route based on clarification need
    if response.need_clarification:
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        return Command(
            goto="write_research_brief", 
            update={"messages": [AIMessage(content=response.verification)]}
        )
```

**Step by step:**
1. Converts the user's messages to a string using `get_buffer_string`
2. Sends the string + prompt to GPT-4.1 with `ClarifyWithUser` structured output
3. The LLM returns: `{need_clarification: bool, question: str, verification: str}`
4. **If clarification needed:**
   - Ends the graph (`goto=END`)
   - Adds the clarifying question as an `AIMessage` to `messages`
   - The user will see the question and can respond, then re-invoke the graph
5. **If no clarification needed:**
   - Proceeds to `write_research_brief`
   - Adds a verification message like "I understand you want to compare React vs Vue..."

**What is `Command`?** A `Command` lets a node do two things at once:
- `update` — Change the state
- `goto` — Choose the next node

This is more powerful than returning a dict (which can only update state, not choose the next node).

#### Node: `write_research_brief` — Generate the Brief

```python
def write_research_brief(state: AgentState):
    """
    Transform the conversation history into a comprehensive research brief.

    Uses structured output to ensure the brief follows the required format
    and contains all necessary details for effective research.
    """
    # Set up structured output model
    structured_output_model = model.with_structured_output(ResearchQuestion)

    # Generate research brief from conversation history
    response = structured_output_model.invoke([
        HumanMessage(content=transform_messages_into_research_topic_prompt.format(
            messages=get_buffer_string(state.get("messages", [])),
            date=get_today_str()
        ))
    ])

    # Update state with generated research brief and pass it to the supervisor
    return {
        "research_brief": response.research_brief,
        "supervisor_messages": [HumanMessage(content=f"{response.research_brief}.")]
    }
```

**What happens:**
1. Takes the full conversation history and formats it as a string
2. Sends it to GPT-4.1 with the `transform_messages_into_research_topic_prompt`
3. Forces structured output using `ResearchQuestion` schema
4. Returns two state updates:
   - `research_brief` — The generated brief (stored for the final report)
   - `supervisor_messages` — Sends the brief as a `HumanMessage` to the supervisor subgraph

**Why `supervisor_messages`?** The supervisor is a subgraph with its own state. It reads `supervisor_messages` to get the research question. By wrapping the brief in a `HumanMessage`, the supervisor sees it as its "user input."

#### Graph Construction

```python
# Build the scoping workflow
deep_researcher_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Add workflow nodes
deep_researcher_builder.add_node("clarify_with_user", clarify_with_user)
deep_researcher_builder.add_node("write_research_brief", write_research_brief)

# Add workflow edges
deep_researcher_builder.add_edge(START, "clarify_with_user")
deep_researcher_builder.add_edge("write_research_brief", END)

# Compile the workflow
scope_research = deep_researcher_builder.compile()
```

**This is a standalone graph** (not used in the full pipeline directly — its nodes are imported individually by `research_agent_full.py`).

```
START ──▶ clarify_with_user
              │
              ├── needs clarification? ──▶ END (with question)
              │
              └── no clarification ──▶ write_research_brief ──▶ END
```

---

## 9. Multi-Agent Supervisor

### 9.1 `multi_agent_supervisor.py` — Parallel Coordination

This is the **heart of the multi-agent system** — the supervisor that delegates research to parallel sub-agents.

```python
"""Multi-agent supervisor for coordinating research across multiple specialized agents.

This module implements a supervisor pattern where:
1. A supervisor agent coordinates research activities and delegates tasks
2. Multiple researcher agents work on specific sub-topics independently
3. Results are aggregated and compressed for final reporting

The supervisor uses parallel research execution to improve efficiency while
maintaining isolated context windows for each research topic.
"""

import asyncio

from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage, 
    BaseMessage, 
    SystemMessage, 
    ToolMessage,
    filter_messages
)
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from reisearch.prompts import lead_researcher_prompt
from reisearch.research_agent import researcher_agent
from reisearch.state_multi_agent_supervisor import (
    SupervisorState, 
    ConductResearch, 
    ResearchComplete
)
from reisearch.utils import get_today_str, think_tool
```

**Key imports:**
- `asyncio` — For running multiple research agents in parallel using `asyncio.gather`
- `researcher_agent` — The compiled research agent graph from `research_agent.py`
- `ConductResearch`, `ResearchComplete` — The tool schemas the supervisor can call
- `Command` — For combined state updates and routing

#### Helper Function

```python
def get_notes_from_tool_calls(messages: list[BaseMessage]) -> list[str]:
    """Extract research notes from ToolMessage objects in supervisor message history.

    This function retrieves the compressed research findings that sub-agents
    return as ToolMessage content. When the supervisor delegates research to
    sub-agents via ConductResearch tool calls, each sub-agent returns its
    compressed findings as the content of a ToolMessage. This function
    extracts all such ToolMessage content to compile the final research notes.

    Args:
        messages: List of messages from supervisor's conversation history

    Returns:
        List of research note strings extracted from ToolMessage objects
    """
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]
```

When the supervisor is done, this function extracts all the compressed research from the ToolMessages. Each ToolMessage contains one sub-agent's findings.

#### Jupyter Compatibility

```python
# Ensure async compatibility for Jupyter environments
try:
    import nest_asyncio
    # Only apply if running in Jupyter/IPython environment
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            nest_asyncio.apply()
    except ImportError:
        pass  # Not in Jupyter, no need for nest_asyncio
except ImportError:
    pass  # nest_asyncio not available, proceed without it
```

**Why?** Jupyter notebooks already run an event loop. When you use `asyncio.gather` inside a Jupyter notebook, it crashes because you can't nest event loops. `nest_asyncio.apply()` patches this by allowing nested event loops. The code is careful to only apply it when actually running in Jupyter.

#### Configuration

```python
supervisor_tools = [ConductResearch, ResearchComplete, think_tool]
supervisor_model = init_chat_model(model="anthropic:claude-sonnet-4-20250514")
supervisor_model_with_tools = supervisor_model.bind_tools(supervisor_tools)

# Maximum number of tool call iterations for individual researcher agents
max_researcher_iterations = 6  # Calls to think_tool + ConductResearch

# Maximum number of concurrent research agents the supervisor can launch
max_concurrent_researchers = 3
```

The supervisor gets three tools:
1. `ConductResearch` — Launch a sub-agent
2. `ResearchComplete` — Signal completion
3. `think_tool` — Strategic thinking

#### Node: `supervisor` (async) — The Decision Maker

```python
async def supervisor(state: SupervisorState) -> Command[Literal["supervisor_tools"]]:
    """Coordinate research activities.

    Analyzes the research brief and current progress to decide:
    - What research topics need investigation
    - Whether to conduct parallel research
    - When research is complete

    Args:
        state: Current supervisor state with messages and research progress

    Returns:
        Command to proceed to supervisor_tools node with updated state
    """
    supervisor_messages = state.get("supervisor_messages", [])

    # Prepare system message with current date and constraints
    system_message = lead_researcher_prompt.format(
        date=get_today_str(), 
        max_concurrent_research_units=max_concurrent_researchers,
        max_researcher_iterations=max_researcher_iterations
    )
    messages = [SystemMessage(content=system_message)] + supervisor_messages

    # Make decision about next research steps
    response = await supervisor_model_with_tools.ainvoke(messages)

    return Command(
        goto="supervisor_tools",
        update={
            "supervisor_messages": [response],
            "research_iterations": state.get("research_iterations", 0) + 1
        }
    )
```

**What happens:**
1. Builds the message list: system prompt (with date, limits) + conversation history
2. Calls Claude Sonnet 4 (async) with the three tools bound
3. The LLM decides what to do:
   - Call `think_tool` to reflect
   - Call `ConductResearch` one or more times to launch sub-agents
   - Call `ResearchComplete` to finish
4. Returns a `Command` that:
   - Goes to `supervisor_tools` (which executes the tool calls)
   - Appends the response to `supervisor_messages`
   - Increments `research_iterations`

#### Node: `supervisor_tools` (async) — Execute Decisions

This is the most complex node — it handles all the supervisor's tool calls.

```python
async def supervisor_tools(state: SupervisorState) -> Command[Literal["supervisor", "__end__"]]:
    """Execute supervisor decisions - either conduct research or end the process.

    Handles:
    - Executing think_tool calls for strategic reflection
    - Launching parallel research agents for different topics
    - Aggregating research results
    - Determining when research is complete

    Args:
        state: Current supervisor state with messages and iteration count

    Returns:
        Command to continue supervision, end process, or handle errors
    """
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1]

    # Initialize variables for single return pattern
    tool_messages = []
    all_raw_notes = []
    next_step = "supervisor"  # Default next step
    should_end = False

    # Check exit criteria first
    exceeded_iterations = research_iterations >= max_researcher_iterations
    no_tool_calls = not most_recent_message.tool_calls
    research_complete = any(
        tool_call["name"] == "ResearchComplete" 
        for tool_call in most_recent_message.tool_calls
    )

    if exceeded_iterations or no_tool_calls or research_complete:
        should_end = True
        next_step = END

    else:
        # Execute ALL tool calls before deciding next step
        try:
            # Separate think_tool calls from ConductResearch calls
            think_tool_calls = [
                tool_call for tool_call in most_recent_message.tool_calls 
                if tool_call["name"] == "think_tool"
            ]

            conduct_research_calls = [
                tool_call for tool_call in most_recent_message.tool_calls 
                if tool_call["name"] == "ConductResearch"
            ]

            # Handle think_tool calls (synchronous)
            for tool_call in think_tool_calls:
                observation = think_tool.invoke(tool_call["args"])
                tool_messages.append(
                    ToolMessage(
                        content=observation,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    )
                )

            # Handle ConductResearch calls (asynchronous)
            if conduct_research_calls:
                # Launch parallel research agents
                coros = [
                    researcher_agent.ainvoke({
                        "researcher_messages": [
                            HumanMessage(content=tool_call["args"]["research_topic"])
                        ],
                        "research_topic": tool_call["args"]["research_topic"]
                    }) 
                    for tool_call in conduct_research_calls
                ]

                # Wait for all research to complete
                tool_results = await asyncio.gather(*coros)

                # Format research results as tool messages
                research_tool_messages = [
                    ToolMessage(
                        content=result.get("compressed_research", "Error synthesizing research report"),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    ) for result, tool_call in zip(tool_results, conduct_research_calls)
                ]

                tool_messages.extend(research_tool_messages)

                # Aggregate raw notes from all research
                all_raw_notes = [
                    "\n".join(result.get("raw_notes", [])) 
                    for result in tool_results
                ]

        except Exception as e:
            print(f"Error in supervisor tools: {e}")
            should_end = True
            next_step = END

    # Single return point with appropriate state updates
    if should_end:
        return Command(
            goto=next_step,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    else:
        return Command(
            goto=next_step,
            update={
                "supervisor_messages": tool_messages,
                "raw_notes": all_raw_notes
            }
        )
```

**Deep breakdown:**

**Step 1: Check exit conditions**
```python
exceeded_iterations = research_iterations >= max_researcher_iterations  # Hit the limit
no_tool_calls = not most_recent_message.tool_calls                       # LLM didn't call tools
research_complete = any(                                                  # LLM called ResearchComplete
    tool_call["name"] == "ResearchComplete" 
    for tool_call in most_recent_message.tool_calls
)
```

Three ways to end:
1. **Iteration limit reached** — Safety valve to prevent infinite loops
2. **No tool calls** — LLM decided not to do anything (shouldn't happen, but handled)
3. **ResearchComplete called** — LLM is satisfied with the research

**Step 2: Execute tool calls**

Tool calls are split into two categories:
- `think_tool` calls — Executed synchronously (they're just string echoes)
- `ConductResearch` calls — Executed in parallel using `asyncio.gather`

**The parallel execution is the key innovation:**
```python
# Create a coroutine for each research agent
coros = [
    researcher_agent.ainvoke({
        "researcher_messages": [HumanMessage(content=topic)],
        "research_topic": topic
    }) 
    for tool_call in conduct_research_calls
]

# Run ALL agents simultaneously
tool_results = await asyncio.gather(*coros)
```

If the supervisor says "research React, Vue, and Svelte," all three agents start searching the web **at the same time**. This is much faster than sequential research.

**Step 3: Package results**

Each sub-agent's `compressed_research` is wrapped in a `ToolMessage` and sent back to the supervisor. The supervisor sees these as tool results and can decide if more research is needed.

**Step 4: Return**
- If ending: Extract all notes from ToolMessages and pass them to the final report
- If continuing: Append tool messages to the conversation and loop back to the supervisor

#### Graph Construction

```python
# Build supervisor graph
supervisor_builder = StateGraph(SupervisorState)
supervisor_builder.add_node("supervisor", supervisor)
supervisor_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_builder.add_edge(START, "supervisor")
supervisor_agent = supervisor_builder.compile()
```

**The supervisor graph:**
```
START ──▶ supervisor
              │
              ▼
         supervisor_tools
              │
              ├── should end? ──▶ END
              │
              └── continue? ──▶ supervisor (loop back)
```

Note: There's no explicit edge from `supervisor_tools` back to `supervisor` or to `END`. The `Command` object handles routing dynamically — the node itself decides where to go next.

---

## 10. Full Pipeline

### 10.1 `research_agent_full.py` — End-to-End Workflow

This is the **main entry point** that wires everything together.

```python
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

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from reisearch.utils import get_today_str
from reisearch.prompts import final_report_generation_prompt
from reisearch.state_scope import AgentState, AgentInputState
from reisearch.research_agent_scope import clarify_with_user, write_research_brief
from reisearch.multi_agent_supervisor import supervisor_agent
```

**Note:** It imports the `clarify_with_user` and `write_research_brief` **functions** (not the compiled graph), and the `supervisor_agent` **compiled graph** (used as a subgraph).

#### Configuration

```python
from langchain.chat_models import init_chat_model
writer_model = init_chat_model(model="openai:gpt-4.1", max_tokens=32000)
```

The final report writer uses GPT-4.1 with 32k max output tokens — reports can be very long.

#### Node: `final_report_generation` — Write the Report

```python
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

    final_report = await writer_model.ainvoke([HumanMessage(content=final_report_prompt)])

    return {
        "final_report": final_report.content, 
        "messages": ["Here is the final report: " + final_report.content],
    }
```

**What happens:**
1. Gets all research notes (compressed findings from all sub-agents)
2. Joins them into a single `findings` string
3. Formats the `final_report_generation_prompt` with:
   - The original research brief
   - All findings
   - Today's date
4. Sends to GPT-4.1 to write the final report
5. Returns:
   - `final_report` — The raw report content
   - `messages` — Adds the report to the user-facing message history

#### Graph Construction — The Full Pipeline

```python
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

# Compile the full workflow
agent = deep_researcher_builder.compile()
```

**The complete pipeline graph:**

```
START
  │
  ▼
clarify_with_user ─────────────────────────┐
  │                                         │
  ├── needs clarification ──▶ END           │
  │   (user sees question,                  │
  │    re-invokes graph                     │
  │    with their answer)                   │
  │                                         │
  └── no clarification ──▶ write_research_brief
                                │
                                ▼
                         supervisor_subgraph
                         (runs the full
                          supervisor +
                          parallel agents)
                                │
                                ▼
                         final_report_generation
                                │
                                ▼
                               END
                         (user gets report)
```

**Key architectural points:**

1. **`supervisor_agent` is a subgraph** — It's a fully compiled graph used as a single node. LangGraph handles state mapping between the parent graph (`AgentState`) and the subgraph (`SupervisorState`). Fields with matching names are automatically shared.

2. **State flows through shared field names:**
   - `supervisor_messages` exists in both `AgentState` and `SupervisorState` → shared
   - `research_brief` exists in both → shared
   - `notes` exists in both → shared
   - `raw_notes` exists in both → shared

3. **The clarification loop uses `Command`:**
   - `clarify_with_user` can jump to `write_research_brief` OR `END`
   - If it jumps to `END`, the user answers the question and re-invokes the graph
   - The second time, `clarify_with_user` sees the answer in `messages` and proceeds

---

## 11. Configuration & Environment

### `.env` — Environment Variables

```
# Required  
OPENAI_API_BASE='https://openrouter.ai/api/v1'
OPENAI_API_KEY='sk-or-v1-...'
TAVILY_API_KEY='tvly-dev-...'
GROQ_API_KEY=gsk_...

# Optional for evaluation and tracing
LANGSMITH_API_KEY='lsv2_pt_...'
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=reisearch
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

| Variable | Purpose |
|---|---|
| `OPENAI_API_BASE` | Base URL for OpenAI-compatible API (using OpenRouter here) |
| `OPENAI_API_KEY` | API key for OpenAI/OpenRouter |
| `TAVILY_API_KEY` | API key for Tavily web search |
| `GROQ_API_KEY` | API key for Groq (fast inference, not used in current code) |
| `LANGSMITH_API_KEY` | API key for LangSmith tracing |
| `LANGSMITH_TRACING` | Enable/disable trace logging to LangSmith |
| `LANGSMITH_PROJECT` | Project name in LangSmith dashboard |

### `__init__.py`

```python
"""Deep Research From Scratch - Tutorial implementation."""
```

Simple package marker. Makes the directory importable as a Python package.

### `pyproject.toml`

```toml
[project]
name = "reisearch"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11,<3.14"
dependencies = [
    "langgraph>=1.0.0",
    "langchain>=1.0.0",
    "langchain-openai>=1.0.0",
    "langchain-anthropic>=1.0.0",
    "langchain_community>=0.4",
    "langchain_tavily>=0.2.12",
    "langchain_mcp_adapters>=0.1.11",
    "pydantic>=2.0.0",
    "rich>=14.0.0",
    "jupyter>=1.0.0",
    "ipykernel>=6.20.0",
    "tavily-python>=0.5.0",
]
```

---

## 12. Execution Flow Walkthrough

Let's trace the exact execution for the query: **"What are the best AI coding assistants in 2025?"**

### Phase 1: Clarification

```
User sends: {"messages": [HumanMessage("What are the best AI coding assistants in 2025?")]}
         │
         ▼
clarify_with_user receives state.messages = [HumanMessage("What are the best...")]
         │
         ▼
GPT-4.1 with ClarifyWithUser schema:
  Input: "Messages: Human: What are the best AI coding assistants in 2025?"
  Output: {
    "need_clarification": false,
    "question": "",
    "verification": "I have enough info. I'll research the best AI coding assistants in 2025."
  }
         │
         ▼
Command(goto="write_research_brief", update={"messages": [AIMessage("I have enough info...")]})
```

### Phase 2: Brief Generation

```
write_research_brief receives:
  state.messages = [
    HumanMessage("What are the best AI coding assistants in 2025?"),
    AIMessage("I have enough info. I'll research...")
  ]
         │
         ▼
GPT-4.1 with ResearchQuestion schema:
  Output: {
    "research_brief": "I want to find the best AI coding assistants available in 2025.
     Consider tools like GitHub Copilot, Cursor, Windsurf, Claude Code, Gemini Code Assist,
     and others. Evaluate them across: code generation quality, language support,
     IDE integration, pricing, unique features, and user reviews.
     Consider all price ranges. Prioritize official websites and reputable
     review sources."
  }
         │
         ▼
Returns: {
  "research_brief": "I want to find the best AI coding assistants...",
  "supervisor_messages": [HumanMessage("I want to find the best AI coding assistants...")]
}
```

### Phase 3: Supervisor Coordination

```
supervisor receives:
  supervisor_messages = [HumanMessage("I want to find the best AI coding assistants...")]
         │
         ▼
Claude Sonnet 4 thinks and calls tools:
  tool_calls = [
    think_tool(reflection="This is a comparison task. I should research
      the top AI coding assistants in parallel..."),
    ConductResearch(research_topic="Research GitHub Copilot as an AI coding assistant
      in 2025, including features, pricing, supported IDEs, code generation quality..."),
    ConductResearch(research_topic="Research Cursor AI coding assistant in 2025,
      including features, pricing, IDE integration, unique capabilities..."),
    ConductResearch(research_topic="Research other AI coding assistants in 2025
      including Windsurf, Claude Code, Gemini Code Assist, Amazon CodeWhisperer...")
  ]
         │
         ▼
supervisor_tools executes:
  1. think_tool → "Reflection recorded: This is a comparison task..."
  2. ConductResearch × 3 → launches 3 parallel researcher_agent instances
         │
         ├──▶ Agent 1 (Copilot): tavily_search → think → tavily_search → compress
         ├──▶ Agent 2 (Cursor): tavily_search → think → tavily_search → compress
         └──▶ Agent 3 (Others): tavily_search → think → tavily_search → compress
         │
         ▼
All 3 agents return compressed_research
         │
         ▼
supervisor sees results, calls think_tool to assess
         │
         ▼
supervisor calls ResearchComplete
         │
         ▼
supervisor_tools detects ResearchComplete → ends with notes
```

### Phase 4: Final Report

```
final_report_generation receives:
  state.notes = [
    "Compressed research about GitHub Copilot...[1] URL...",
    "Compressed research about Cursor...[1] URL...",
    "Compressed research about Windsurf, Claude Code...[1] URL..."
  ]
  state.research_brief = "I want to find the best AI coding assistants..."
         │
         ▼
GPT-4.1 writes a comprehensive markdown report:
  # Best AI Coding Assistants in 2025
  ## GitHub Copilot
  ...detailed analysis with [1] citations...
  ## Cursor
  ...detailed analysis with [2] citations...
  ## Other Notable Assistants
  ### Windsurf
  ...
  ### Claude Code
  ...
  ## Comparison
  ...
  ### Sources
  [1] GitHub Copilot: https://...
  [2] Cursor: https://...
         │
         ▼
Returns: {
  "final_report": "# Best AI Coding Assistants in 2025...",
  "messages": ["Here is the final report: # Best AI Coding Assistants in 2025..."]
}
```

---

## Summary of Models Used

| Model | Where Used | Why |
|---|---|---|
| `anthropic:claude-sonnet-4-20250514` | Research agent LLM calls, Supervisor decisions | Excellent tool calling, reasoning, and research |
| `openai:gpt-4.1` | Brief generation, Research compression, Final report | Strong long-form writing, 32k output tokens |
| `openai:gpt-4.1-mini` | Webpage summarization | Fast and cheap for simple summarization |

## Summary of All Files

| File | Lines | Role |
|---|---|---|
| `state_scope.py` | 63 | Top-level state + structured output schemas |
| `state_research.py` | 66 | Researcher state + output schemas |
| `state_multi_agent_supervisor.py` | 47 | Supervisor state + delegation tools |
| `utils.py` | 239 | Tavily search, summarization, think tool |
| `prompts.py` | 573 | All prompt templates |
| `research_agent.py` | 145 | Single web search research agent |
| `research_agent_mcp.py` | 209 | MCP file-based research agent |
| `research_agent_scope.py` | 105 | Clarification + brief generation |
| `multi_agent_supervisor.py` | 249 | Supervisor with parallel sub-agents |
| `research_agent_full.py` | 75 | Full pipeline entry point |
| `__init__.py` | 1 | Package marker |
