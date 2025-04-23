from langchain.tools import BaseTool
from typing import Callable, Dict, Any
import uuid

class RequestTrackedTool(BaseTool):
    """Tool wrapper that injects request_id into each tool call."""
    
    tool_function: Callable
    request_id: str
    
    def _run(self, *args, **kwargs):
        # Inject request_id into all tool calls
        kwargs["request_id"] = self.request_id
        return self.tool_function(*args, **kwargs)


def retrieve_complete_sources(sources: list[str], request_id: str) -> str:
    """
    retrieves the list of sources (given by id) and merges the complete content in markdown format

    Args:
        sources (list[str]): list of source IDs

    Returns:
        str: combined source content in markdown format
    """
    


# Usage example
def create_tools_for_request(request_id):

    
    # Wrap each tool with the request_id
    tools = [
        RequestTrackedTool(
            name="search",
            description="Search for information",
            tool_function=search_tool,
            request_id=request_id
        )
    ]
    
    return tools, request_id
