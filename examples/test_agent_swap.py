import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Temporary sanity check — safe to share, never prints the key itself
print(f"[debug] .env path: {env_path} | exists: {env_path.exists()} | ANTHROPIC_API_KEY loaded: {bool(os.getenv('ANTHROPIC_API_KEY'))}")

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from backend.swap.tool import swap_tool

def run_agent_test():
    # 1. Initialize Claude Model
    llm = ChatAnthropic(model="claude-sonnet-5", temperature=0)

    # 2. Bind swap tool
    tools = [swap_tool]

    # 3. Build Agent
    agent_executor = create_react_agent(llm, tools)

    # 4. Execute User Request
    print("\n--- Prompting AI Agent ---\n")
    user_prompt = "Please swap 75 USDT to USDC with a 0.5% slippage tolerance."
    
    # LangGraph uses a "messages" state dictionary
    response = agent_executor.invoke({"messages": [("user", user_prompt)]})

    print("\n=== FINAL AGENT ANSWER ===")
    print(response["messages"][-1].content)

if __name__ == "__main__":
    run_agent_test()
    