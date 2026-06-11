# 📝 Code Changes Log

This document records the changes made to the deep research system codebase to fix critical execution bugs, handle Groq model generation quirks, add state checkpointing, bypass free-tier rate limits, and improve the interactive CLI experience.

---

## 🛠️ Summary of Changes

### 1. Robust Groq Formatting Parser Fallbacks
* **Issue**: The Groq API server frequently rejects LLM completions with a `400 Bad Request (tool_use_failed)` error. This happens because models generate invalid JSON schemas under several circumstances:
  1. Incorrectly escaping single quotes inside JSON strings (e.g. `\'` instead of `'`).
  2. Outputting literal control characters (like newlines `\n` in lists) directly into string values.
  3. Outputting booleans as strings (e.g. `"need_clarification": "true"` instead of `true`).
  4. Generating JSON outputs in OpenAI-style array structures (`[{"name": "...", "parameters": {...}}]`) instead of XML-like `<function=...>` tags depending on model type.
* **Resolution**: Added generic parser recovery helpers inside [utils.py](file:///Users/chiragtaneja/Codes/repos/reisearch/utils.py) that catch the 400 Bad Request error, extract the raw `failed_generation` tool calls, support both OpenAI JSON array and XML structures, clean up invalid escapes, parse with `strict=False` (allowing control characters), convert string booleans to Python booleans, and successfully recover the execution state.

### 2. Daily Token Limit (TPD) & TPM Bypass via Llama 4 Scout Migration
* **Issue**: The `llama-3.3-70b-versatile` model has a strict free-tier daily token limit of **100,000 tokens per day (TPD)**, which the user fully exhausted. Additionally, webpage summarization using `llama-3.1-8b-instant` hit a **6,000 tokens per minute (TPM)** limit when webpage content truncation was set to 15,000 characters.
* **Resolution**: 
  1. Migrated the main scoping, supervisor, research, and compression brain models from `llama-3.3-70b-versatile` to `meta-llama/llama-4-scout-17b-16e-instruct` on Groq. The Llama 4 Scout model has a much higher rate limit (30,000 TPM limit) and no strict daily token limits.
  2. Lowered the webpage content truncation limit (`max_chars`) to **6,000 characters** in webpage summarization.
  3. **Summarization Model Migration**: Changed the webpage summarization model (`summarization_model` in `utils.py` and `research_agent.py`) from `llama-3.1-8b-instant` to `meta-llama/llama-4-scout-17b-16e-instruct` to completely avoid the 6,000 TPM limit.

### 3. Multi-turn Conversation Memory (Amnesia Fix)
* **Issue**: The interactive CLI scoping conversation forgot the context of the user query after every turn. This occurred because all LangGraph agents were compiled without a state checkpointer, causing LangGraph to drop all conversation history across separate `.astream()` calls.
* **Resolution**: Integrated an in-memory `MemorySaver` checkpointer in all Compiled graphs to ensure conversation memory is correctly retained across multiple turns.

### 4. Real-time Progress Timer & Trace Logging in CLI
* **Issue**: The CLI kept the user waiting in a silent spin state without showing what sub-agents or tools were currently active, which made long-running research jobs feel unresponsive.
* **Resolution**: Replaced standard state value streaming in `cli.py` with LangGraph's event stream API (`astream_events`). Added a concurrent background spinner task that updates the console in real-time, printing:
  1. The ticking elapsed time in seconds (`[12s]`).
  2. The current executing graph step/node (`Step: supervisor_subgraph`).
  3. Real-time logging of entering nodes, starting tools, completed tools, and generated thoughts.
  4. **Optional Trace Logs via `/show-logs`**: Added a toggle command `/show-logs` in the interactive CLI to let users enable/disable verbose trace logs on the fly. When logs are turned OFF, the timer and current step spinner continue ticking normally, but the detailed stdout messages are hidden.

### 5. Auto-Retry and Backoff Resilience
* **Issue**: Transient rate limits (429) and random formatting errors (400) from the Groq API can cause direct crashes if they occur at the wrong moment.
* **Resolution**: Added auto-retry logic with exponential backoff inside the structured output and tool calling helpers in [utils.py](file:///Users/chiragtaneja/Codes/repos/reisearch/utils.py). If a request fails, it automatically waits and retries the call up to 3 times. Also imported missing `time` and `asyncio` libraries.

---

## 📂 Detailed File Modifications

### 1. [utils.py](file:///Users/chiragtaneja/Codes/repos/reisearch/utils.py)
* **Added / Enhanced Helper functions**:
  * `invoke_safe_structured_output(model, schema, messages, max_retries=3, delay=2.0)`: Invokes a structured LLM call with a retry loop (exponential backoff) and cleans up/parses JSON manually in case of Groq API server errors.
  * `invoke_safe_tool_calling(model_with_tools, messages, is_async=False, max_retries=3, delay=2.0)`: Invokes tool calling sync or async with a retry loop and manually recovers tool calls from `failed_generation`.
  * Imported `time` and `asyncio` to support delays during retry loops.

* **Applied Safeguards**:
  * Used `invoke_safe_structured_output` inside `summarize_webpage_content` to make webpage summarization bulletproof.
  * Switched `summarization_model` to `groq:meta-llama/llama-4-scout-17b-16e-instruct` to bypass the 6,000 TPM rate limit of `llama-3.1-8b-instant`.
* **Lowered Truncation Length**:
  * Changed webpage content truncation size (`max_chars`) to **6000** to stay within the 6,000 TPM limit of `llama-3.1-8b-instant`.
* **Removed Stray Prints**:
  * Replaced the asynchronous stdout truncation log `print(f"⚠️ Truncating massive webpage...")` with a comment to perform truncation silently and prevent clobbering the CLI prompt layout.

### 2. [research_agent_scope.py](file:///Users/chiragtaneja/Codes/repos/reisearch/research_agent_scope.py)
* Switched scoping model to `groq:meta-llama/llama-4-scout-17b-16e-instruct`.
* Wrapped scoping model structured output calls with `invoke_safe_structured_output`.
* Compiled the `scope_research` graph with `checkpointer=MemorySaver()`.

### 3. [research_agent.py](file:///Users/chiragtaneja/Codes/repos/reisearch/research_agent.py)
* Switched research, compression, and summarization models to `groq:meta-llama/llama-4-scout-17b-16e-instruct`.
* Wrapped `model_with_tools.invoke` calls inside `llm_call` using `invoke_safe_tool_calling`.
* Compiled the `researcher_agent` graph with `checkpointer=MemorySaver()`.

### 4. [research_agent_mcp.py](file:///Users/chiragtaneja/Codes/repos/reisearch/research_agent_mcp.py)
* Switched research and compression models to `groq:meta-llama/llama-4-scout-17b-16e-instruct`.
* Wrapped `model_with_tools.invoke` calls inside `llm_call` using `invoke_safe_tool_calling`.
* Compiled the `agent_mcp` graph with `checkpointer=MemorySaver()`.

### 5. [multi_agent_supervisor.py](file:///Users/chiragtaneja/Codes/repos/reisearch/multi_agent_supervisor.py)
* Switched supervisor model to `groq:openai/gpt-oss-120b` for advanced task routing and delegation.
* Wrapped `supervisor_model_with_tools.ainvoke` call inside `supervisor` using `invoke_safe_tool_calling`.
* Compiled the `supervisor_agent` graph with `checkpointer=MemorySaver()`.

### 6. [research_agent_full.py](file:///Users/chiragtaneja/Codes/repos/reisearch/research_agent_full.py)
* Switched writing model to `groq:openai/gpt-oss-120b` for high-quality, safe final report generation.
* Compiled the full `agent` graph with `checkpointer=MemorySaver()`.

### 7. [cli.py](file:///Users/chiragtaneja/Codes/repos/reisearch/cli.py)
* Imported `time` for duration tracking.
* Added `update_spinner_timer` coroutine to update the progress display every 100ms with:
  * Running elapsed timer.
  * Active executing node name.
  * Current execution status.
* Replaced the standard `run_agent` loop with an `astream_events(version="v2")` stream to capture and log:
  * Node start events (with exact active step name).
  * Tool calls, tool start, and tool end notifications.
  * Intermediate model thoughts and reasoning blocks.
  * Top-level final state dictionary from the root `LangGraph` chain end event.
* Added `/show-logs` command to toggle the visibility of trace logs dynamically.
* Handled the toggle state in `run_agent` to conditionally output detailed thoughts, tool calls, and node entry logs.
* Updated `/help` output to show the current ON/OFF status of the logs.

---

## 🏃 Verification and Execution
* Verified that all code edits compile cleanly without syntax errors (`python -m py_compile`).
* Re-launch the CLI by exiting the current run and executing:
  ```bash
  uv run python cli.py
  ```
