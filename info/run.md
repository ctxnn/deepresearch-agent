# How to Run Deep Research Agents

You have two options for running the agents in this repository: using the visual **LangGraph Studio** UI (highly recommended), or running them directly in your **Terminal**.

---

## Option 1: Run in LangGraph Studio (Recommended Visual UI)

LangGraph Studio is a local web interface that lets you chat with your agents, edit their state in real-time, and see exactly which tools they are calling.

1. Ensure your API keys are set in your `.env` file (e.g., `GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGSMITH_API_KEY`).
2. Open your terminal in the `reisearch` repository.
3. Run this exact command to start the studio:
   ```bash
   uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev
   ```
4. This will automatically open a browser window to [smith.langchain.com/studio](https://smith.langchain.com/studio).
5. In the top left corner of the UI, you will see a dropdown where you can select which agent to interact with:
   - `scoping_agent`
   - `research_agent`
   - `supervisor_agent`
   - `full_agent`
6. Select an agent, type a prompt, and watch the multi-agent system think and execute!

---

## Option 2: Run in your Terminal

If you just want a quick CLI interface without the UI, you can use the provided `run.py` script.

1. Open your terminal in the `reisearch` repository.
2. Run the script using `uv`:
   ```bash
   uv run python run.py
   ```
3. Type in a research request when prompted.
4. You will see the agent's thought process stream directly into your terminal, culminating in the final research brief or report.

> [!TIP]
> **Customizing the Terminal Runner**
> By default, `run.py` runs the `scoping_agent`. If you want to run the full deep researcher instead, open `run.py` and change the import to grab `agent` from `research_agent_full.py` and invoke that instead!

---

## Option 3: Interactive CLI (Premium TUI)

For a premium, interactive terminal experience similar to Claude Code or OpenCode, use the interactive CLI. This mode offers a continuous chat loop, up/down arrow history, slash commands, and real-time streaming with beautiful animations.

1. Open your terminal in the `reisearch` repository.
2. Run the interactive CLI:
   ```bash
   uv run python cli.py
   ```
3. Type `/help` to see all available commands.
4. You can hot-swap the active agent seamlessly by typing `/agent full` or `/agent supervisor`.
5. Enjoy real-time streaming of the agent's thought process and beautifully formatted markdown reports!
