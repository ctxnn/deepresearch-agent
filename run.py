import asyncio
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from research_agent_scope import scope_research

async def main():
    print("Welcome to Deep Research (Terminal Edition)!")
    print("This script will run the Scoping Agent on your query.")
    print("-" * 50)
    
    query = input("Enter your research request: ")
    
    # Run the scoping agent
    print("\nRunning Scoping Agent...")
    initial_state = {
        "messages": [HumanMessage(content=query)]
    }
    
    async for event in scope_research.astream(initial_state, config={"configurable": {"thread_id": "1"}}):
        for node_name, node_state in event.items():
            print(f"\n--- Output from node: {node_name} ---")
            if "messages" in node_state and node_state["messages"]:
                print(node_state["messages"][-1].content)
            elif "research_brief" in node_state:
                print("\n[RESEARCH BRIEF GENERATED]")
                print(node_state["research_brief"])

if __name__ == "__main__":
    asyncio.run(main())
