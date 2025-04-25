from langchain.tools import BaseTool
from typing import Callable, Dict, Any
import asyncio
import uuid

from core.schema import UpdateState
from repository import RedisRepository
from core.db import get_sources


def with_redis_updates(func):
    """Decorator that enables Redis state updates from within tool functions."""
    async def wrapper(*args, **kwargs):
        request_id = kwargs.get("request_id")
        if not request_id:
            raise ValueError("No request_id provided for tool execution")

        redis_repo: RedisRepository = kwargs.get("redis_repo", None)
        if redis_repo is None:
            raise ValueError("Redis is not accessible")

        def update_state(state_update: UpdateState):
            redis_repo.update_record(
                record_id=request_id, state=state_update.model_dump())

        kwargs["update_state"] = update_state

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
    redis_repo: RedisRepository

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
    update_state = kwargs['update_state']
    sources = get_sources(source_ids)

    source_titles = [source.title for source in sources]
    update_state(UpdateState(type="sources", content=source_titles))

    sources_description = ""
    for source in sources:
        sources_description += f"**{source.title}:**\n{source.content}\n\n"

    return sources_description


@with_redis_updates
def retrieve_sources_summary(source_ids: list[str], **kwargs) -> str:
    """
    retrieves the list of sources (given by id) and merges only the summary content in markdown format

    Args:
        sources (list[str]): list of source IDs

    Returns:
        str: combined source content in markdown format
    """
    update_state = kwargs['update_state']
    sources = get_sources(source_ids)

    source_titles = [source.title for source in sources]
    update_state(UpdateState(type="sources", content=source_titles))

    sources_description = ""
    for source in sources:
        sources_description += f"**{source.title}:**\n{source.summary}\n\n"

    return sources_description


def create_tools_for_request(request_id: str, redis_repo: RedisRepository):
    tools = [
        RequestTrackedTool(
            name="retrieve_sources_complete",
            description="retrieves the list of sources (given by id) and merges the complete content in markdown format",
            tool_function=retrieve_sources_complete,
            request_id=request_id,
            redis_repo=redis_repo
        ),
        RequestTrackedTool(
            name="retrieve_sources_summary",
            description="retrieves the list of sources (given by id) and merges only the summary content in markdown format",
            tool_function=retrieve_sources_summary,
            request_id=request_id,
            redis_repo=redis_repo
        )
    ]

    return tools
