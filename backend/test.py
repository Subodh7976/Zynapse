# Create server parameters for stdio connection
from langchain_mcp_tools import convert_mcp_to_langchain_tools

from langgraph.prebuilt import create_react_agent
from anyio import get_cancelled_exc_class, CancelScope

# from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model

model = init_chat_model(model="gpt-4o", api_key="", model_provider="openai")

mcp_servers = {
    "search": { # https://github.com/nickclyde/duckduckgo-mcp-server/tree/main
        "command": "uvx",
        "args": ["duckduckgo-mcp-server"]
    },
  "arXivPaper": { # https://github.com/daheepk/arxiv-paper-mcp
    "command": "uvx",
    "args": [
      "--from",
      "arxiv-paper-mcp",
      "arxiv-mcp"
    ]
  }
}

from langchain.tools import tool
from typing import Optional, Type
import asyncio

@tool
def addition(num1: int, num2: int):
    """Addition of two numbers."""
    return num1 + num2

@tool
def multiply(num1: int, num2: int):
    """Multiply two numbers."""
    return num1 * num2

local_tools = [addition, 
               multiply]

async def run():
    cleanup = None
    try:
        tools, cleanup = await convert_mcp_to_langchain_tools(mcp_servers)
        agent = create_react_agent(model, tools, prompt="You have multiple available tools:\n* Use search tool for search anything from the web and fetch content for any specific website\n* Use Arxivpaper for finding latest research, related to certain query or domain.")
        agent_response = await agent.ainvoke({"messages": "Think carefully and answer - What is the latest research on LLMs?"})
        print(agent_response['messages'][-1].content)
    except:
        pass
    finally:
        if cleanup is not None:
            await cleanup()
    print("Error after this")


def main():
    asyncio.run(run())

if __name__=="__main__":
    main()