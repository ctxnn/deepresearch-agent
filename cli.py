import asyncio
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

async def run_agent(agent_name, query, session_id):
    agent = AGENTS.get(agent_name)
    if not agent:
        console.print(f"[bold red]Unknown agent: {agent_name}[/]")
        return

    initial_state = {"messages": [HumanMessage(content=query)]}
    final_state = {}
    
    console.print()
    with Live(Spinner("dots", text=f"Agent '{agent_name}' is working..."), refresh_per_second=10) as live:
        try:
            num_messages_seen = 1 # Skip the initial HumanMessage we just added
            async for state in agent.astream(initial_state, config={"configurable": {"thread_id": session_id}}, stream_mode="values"):
                final_state = state
                live.update(Spinner("dots", text=f"Agent '{agent_name}' is working..."))
                
                if "messages" in state and state["messages"]:
                    if len(state["messages"]) > num_messages_seen:
                        for i in range(num_messages_seen, len(state["messages"])):
                            last_message = state["messages"][i]
                            
                            # Print tool calls if any
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                for tc in last_message.tool_calls:
                                    tool_name = tc.get("name", "UnknownTool")
                                    args_str = str(tc.get("args", {}))
                                    if len(args_str) > 100:
                                        args_str = args_str[:97] + "..."
                                    console.print(f"[dim cyan]🔧 Calling tool: {tool_name} ({args_str})[/]")
                                    
                            elif isinstance(last_message, ToolMessage):
                                console.print(f"[dim]✓ Tool {last_message.name} finished.[/]")
                                    
                            elif isinstance(last_message, AIMessage) and last_message.content:
                                content_str = last_message.content
                                # Limit thought output length to avoid flooding the screen
                                if len(content_str) > 150:
                                    content_str = content_str[:147] + "..."
                                console.print(f"[dim italic magenta]💭 Thought: {content_str}[/]")
                        
                        num_messages_seen = len(state["messages"])
                        
            live.update(Spinner("dots", text="Formatting final output..."))
            await asyncio.sleep(0.5)
            
        except Exception as e:
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
                
            elif command == '/help':
                help_text = """
[bold]Available Commands:[/bold]
[yellow]/agent <name>[/yellow] - Switch the active agent. Available options:
  - [cyan]scope[/cyan]: Generates a research brief from a vague query
  - [cyan]research[/cyan]: Solves a specific research brief using web search
  - [cyan]supervisor[/cyan]: Delegates multiple sub-research tasks in parallel
  - [cyan]full[/cyan]: The complete end-to-end multi-agent system

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
                await run_agent(current_agent, user_input, session_id)
                
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/]")
            break

if __name__ == "__main__":
    asyncio.run(main())
