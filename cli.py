import asyncio
import time
from dotenv import load_dotenv
load_dotenv()

import uuid
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.align import Align
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Import the agents
from research_agent_scope import scope_research
from research_agent import researcher_agent
from multi_agent_supervisor import supervisor_agent
from research_agent_full import agent as full_agent

AGENTS = {
    "scope": scope_research,
    "research": researcher_agent,
    "supervisor": supervisor_agent,
    "full": full_agent
}

console = Console()

async def update_spinner_timer(live, agent_name, start_time, status):
    """Periodically update the spinner with real-time elapsed time and status."""
    while True:
        elapsed = int(time.time() - start_time)
        step_text = f" [bold yellow]•[/] Step: [cyan]{status['node']}[/]" if status['node'] else ""
        details_text = f"\n  [dim]{status['details']}[/]" if status['details'] else ""
        live.update(Spinner("dots", text=f"Agent '{agent_name}' is working... [bold green]{elapsed}s[/]{step_text}{details_text}"))
        await asyncio.sleep(0.1)

async def run_agent(agent_name, query, session_id, show_logs=True):
    agent = AGENTS.get(agent_name)
    if not agent:
        console.print(f"[bold red]Unknown agent: {agent_name}[/]")
        return

    initial_state = {"messages": [HumanMessage(content=query)]}
    final_state = {}
    
    console.print()
    status = {"node": "Initializing", "details": ""}
    start_time = time.time()
    
    with Live(Spinner("dots", text=f"Agent '{agent_name}' is working... [bold green]0s[/]"), refresh_per_second=10) as live:
        timer_task = asyncio.create_task(update_spinner_timer(live, agent_name, start_time, status))
        
        try:
            async for event in agent.astream_events(initial_state, version="v2", config={"configurable": {"thread_id": session_id}}):
                kind = event.get("event")
                name = event.get("name")
                
                if kind == "on_chain_start":
                    metadata = event.get("metadata", {})
                    langgraph_node = metadata.get("langgraph_node")
                    if langgraph_node:
                        status["node"] = langgraph_node
                        status["details"] = f"Entering step '{langgraph_node}'"
                        if show_logs:
                            live.console.print(f"[dim]➔ Entering step: [bold cyan]{langgraph_node}[/bold cyan][/dim]")
                        
                elif kind == "on_chat_model_end":
                    output = event.get("data", {}).get("output", {})
                    content = getattr(output, "content", "")
                    tool_calls = getattr(output, "tool_calls", [])
                    
                    if content:
                        thought_str = content
                        if len(thought_str) > 150:
                            thought_str = thought_str[:147] + "..."
                        status["details"] = f"Thought: {thought_str}"
                        if show_logs:
                            live.console.print(f"[dim italic magenta]💭 Thought: {thought_str}[/dim italic magenta]")
                        
                    if tool_calls:
                        for tc in tool_calls:
                            tool_name = tc.get("name", "UnknownTool")
                            args_str = str(tc.get("args", {}))
                            if len(args_str) > 100:
                                args_str = args_str[:97] + "..."
                            status["details"] = f"Calling tool: {tool_name}"
                            if show_logs:
                                live.console.print(f"[dim cyan]🔧 Calling tool: {tool_name} ({args_str})[/dim cyan]")
                            
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = str(event.get("data", {}).get("input", ""))
                    if len(tool_input) > 80:
                        tool_input = tool_input[:77] + "..."
                    status["details"] = f"Tool '{tool_name}' starting ({tool_input})"
                    
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    status["details"] = f"Tool '{tool_name}' completed"
                    if show_logs:
                        live.console.print(f"[dim]✓ Tool {tool_name} finished.[/dim]")
                    
                elif kind == "on_chain_end" and name == "LangGraph":
                    final_state = event.get("data", {}).get("output", {})
                    
            timer_task.cancel()
            live.update(Spinner("dots", text=f"Formatting final output... [bold green]{int(time.time() - start_time)}s[/]"))
            await asyncio.sleep(0.5)
            
        except Exception as e:
            timer_task.cancel()
            console.print(f"[bold red]An error occurred: {str(e)}[/]")
            return

    # Print final state gracefully
    console.print()
    if "final_report" in final_state and final_state["final_report"]:
        console.print(Panel(Markdown(final_state["final_report"]), title="[bold green]Final Research Report[/]", border_style="green"))
    elif "research_brief" in final_state and final_state["research_brief"]:
        console.print(Panel(Markdown(final_state["research_brief"]), title="[bold green]Research Brief[/]", border_style="green"))
    elif "notes" in final_state and final_state["notes"]:
        notes_str = str(final_state["notes"])
        if len(notes_str) > 2000:
            notes_str = notes_str[:1997] + "..."
        console.print(Panel(Markdown(notes_str), title="[bold green]Supervisor Notes[/]", border_style="green"))
    elif "messages" in final_state and final_state["messages"]:
        # Fallback to printing the last message if no specific output fields are found
        last_msg = final_state["messages"][-1]
        if isinstance(last_msg, AIMessage) and last_msg.content:
             console.print(Panel(Markdown(last_msg.content), title="[bold green]Agent Response[/]", border_style="green"))

BANNER = """[bold cyan]
          _                         _     
 _ __ ___(_)___  ___  __ _ _ __ ___| |__  
| '__/ _ \\ / __|/ _ \\/ _` | '__/ __| '_ \\ 
| | |  __/ \\__ \\  __/ (_| | | | (__| | | |
|_|  \\___|_|___/\\___|\\__,_|_|  \\___|_| |_|[/bold cyan]
"""

def print_welcome_screen():
    console.clear()
    term_height = console.height
    # The banner + panel is roughly 12 lines tall now.
    pad_top = max(0, (term_height - 12) // 2)
    if pad_top > 0:
        print("\n" * (pad_top - 1))
        
    console.print(Align.center(BANNER))
    panel = Panel.fit("[bold blue]Deep Research Interactive CLI[/bold blue]\n[dim]A premium TUI for the Deep Research Multi-Agent System.[/]\n\nType [yellow]/help[/yellow] for commands.", border_style="blue")
    console.print(Align.center(panel))
    print("\n")

async def main():
    print_welcome_screen()
    
    session = PromptSession()
    current_agent = "scope"
    session_id = str(uuid.uuid4())
    show_logs = True
    
    while True:
        try:
            # We use prompt_async to integrate cleanly with the asyncio event loop
            user_input = await session.prompt_async(HTML(f"<b><ansigreen>[{current_agent}]</ansigreen></b> ❯ "))
            
            if not user_input.strip():
                continue
                
            command = user_input.strip()
            
            if command in ['/exit', '/quit']:
                console.print("[yellow]Goodbye![/]")
                break
                
            elif command == '/clear':
                print_welcome_screen()
                session_id = str(uuid.uuid4()) # Start a fresh conversation memory
                console.print(Align.center("[green]Screen cleared and session reset.[/green]"))
                
            elif command == '/show-logs':
                show_logs = not show_logs
                status_str = "ON" if show_logs else "OFF"
                console.print(f"[green]Real-time trace logs are now [bold]{status_str}[/bold].[/green]")
                
            elif command == '/help':
                help_text = f"""
[bold]Available Commands:[/bold]
[yellow]/agent <name>[/yellow] - Switch the active agent. Available options:
  - [cyan]scope[/cyan]: Generates a research brief from a vague query
  - [cyan]research[/cyan]: Solves a specific research brief using web search
  - [cyan]supervisor[/cyan]: Delegates multiple sub-research tasks in parallel
  - [cyan]full[/cyan]: The complete end-to-end multi-agent system

[yellow]/show-logs[/yellow] - Toggle real-time trace logs ON/OFF (currently: [bold]{"ON" if show_logs else "OFF"}[/bold])
[yellow]/clear[/yellow] - Clear the screen and reset conversation memory
[yellow]/exit[/yellow] - Quit the CLI
"""
                console.print(Panel(help_text, title="Help", border_style="yellow"))
                
            elif command.startswith('/agent '):
                new_agent = command.split(' ', 1)[1].strip()
                if new_agent in AGENTS:
                    current_agent = new_agent
                    console.print(f"[green]Switched active agent to: [bold]{current_agent}[/bold][/green]")
                else:
                    console.print(f"[red]Unknown agent '{new_agent}'. Available: {', '.join(AGENTS.keys())}[/red]")
                    
            elif command.startswith('/'):
                console.print("[red]Unknown command. Type /help for options.[/red]")
                
            else:
                # It's a real query
                await run_agent(current_agent, user_input, session_id, show_logs=show_logs)
                
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/]")
            break

if __name__ == "__main__":
    asyncio.run(main())
