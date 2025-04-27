# Create server parameters for stdio connection
from langchain_mcp_tools import convert_mcp_to_langchain_tools

from langgraph.prebuilt import create_react_agent
from anyio import get_cancelled_exc_class, CancelScope

# from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain.tools import BaseTool
from typing import Callable, Dict, Any
import asyncio


def with_redis_updates(func):
    """Decorator that enables Redis state updates from within tool functions."""
    async def wrapper(*args, **kwargs):
        request_id = kwargs.get("request_id")
        if not request_id:
            raise ValueError("No request_id provided for tool execution")

        redis_repo: str = kwargs.get("redis_repo", None)
        if redis_repo is None:
            raise ValueError("Redis is not accessible")

        # def update_state(state_update: Any):
        #     redis_repo.update_record(
        #         record_id=request_id, state=state_update.model_dump())

        # kwargs["update_state"] = update_state

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            return result
        except Exception as e:
            print("Error at tool call - ", e)
            raise e

    return wrapper


class RequestTrackedTool(BaseTool):
    """Tool wrapper that injects request_id into each tool call."""

    tool_function: Callable
    request_id: str
    redis_repo: str

    def _run(self, *args, **kwargs):
        kwargs["request_id"] = self.request_id
        kwargs['redis_repo'] = self.redis_repo
        return self.tool_function(*args, **kwargs)

    async def _arun(self, *args, **kwargs):
        kwargs["request_id"] = self.request_id
        kwargs['redis_repo'] = self.redis_repo
        return await self.tool_function(*args, **kwargs)

@with_redis_updates
def retrieve_sources_complete(source_ids: list[str], **kwargs) -> str:
    """
    retrieves the list of sources (given by id) and merges the complete content in markdown format

    Args:
        source_ids (list[str]): list of source IDs

    Returns:
        str: combined source content in markdown format
    """
    # update_state = kwargs['update_state']
    # sources = 

    # source_titles = [source.title for source in sources]
    # # update_state(UpdateState(type="sources", content=source_titles))

    # sources_description = ""
    # for source in sources:
    #     sources_description += f"**{source.title}:**\n{source.content}\n\n"

    return "Placeholder sources description"


@with_redis_updates
def retrieve_sources_summary(source_ids: list[str], **kwargs) -> str:
    """
    retrieves the list of sources (given by id) and merges only the summary content in markdown format

    Args:
        source_ids (list[str]): list of source IDs

    Returns:
        str: combined source content in markdown format
    """
    # update_state = kwargs['update_state']
    # sources = get_sources(source_ids)

    # source_titles = [source.title for source in sources]
    # update_state(UpdateState(type="sources", content=source_titles))

    # sources_description = ""
    # for source in sources:
    #     sources_description += f"**{source.title}:**\n{source.summary}\n\n"

    return "Placeholder sources summary"

from pydantic import BaseModel, Field

class SourceIdsInput(BaseModel):
    source_ids: list[str] = Field(..., description="List of source IDs to retrieve")

def create_tools_for_request(request_id: str, redis_repo: str):
    tools = [
        RequestTrackedTool(
            name="retrieve_sources_complete",
            description="retrieves the list of sources (given by id) and merges the complete content in markdown format.     Args: source_ids (list[str]): list of source IDs",
            tool_function=retrieve_sources_complete,
            args_schema=SourceIdsInput,
            request_id=request_id,
            redis_repo=redis_repo
        ),
        RequestTrackedTool(
            name="retrieve_sources_summary",
            description="retrieves the list of sources (given by id) and merges only the summary content in markdown format.  Args: source_ids (list[str]): list of source IDs",
            tool_function=retrieve_sources_summary,
            request_id=request_id,
            args_schema=SourceIdsInput,
            redis_repo=redis_repo
        )
    ]

    return tools



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
        local_tools = create_tools_for_request("test", 'test')
        agent = create_react_agent(model, local_tools, prompt="You have multiple available tools:\n* Use search tool for search anything from the web and fetch content for any specific website\n* Use Arxivpaper for finding latest research, related to certain query or domain.\n* Given the only source user has - ID ('test-source-v2'), Title ('Test Source'), Brief ('Only available source') it can be used for fetching information or context related to user query and can be used in retrieve sources tools")
        agent_response = await agent.ainvoke({"messages": "Summarize the sources provided."})
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