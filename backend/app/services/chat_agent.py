from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from config import CHAT_AGENT_MODEL
from helper.utils import build_sources_description
from core.schema import UpdateState
from .tools import create_tools_for_request
from .mcp import create_mcp_tools
from .prompts import CHAT_AGENT_PROMPT

llm = ChatGoogleGenerativeAI(model=CHAT_AGENT_MODEL, temperature=0.7)
prompt = PromptTemplate(
    template=CHAT_AGENT_PROMPT,
    input_variables=['sources']
)

class MCPToolsManager:
    _instance = None
    _tools = None
    _cleanup = None
    _initialized = False
    
    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = MCPToolsManager()
        return cls._instance
    
    async def ensure_initialized(self):
        if not self._initialized:
            print("Retrying, you stupid")
            self._tools, self._cleanup = await create_mcp_tools()
            self._initialized = True
    
    def get_tools(self):
        return self._tools
    
    async def cleanup_resources(self):
        if self._cleanup and self._initialized:
            await self._cleanup()
            self._tools = None
            self._cleanup = None
            self._initialized = False


async def agent_response(query: str, sources: str, tools: list):
    agent = create_react_agent(
        llm, tools, prompt=prompt.format(sources=sources))
    response_generator = agent.astream(
        {"messages": query}, stream_mode="messages")

    message = ""
    async for chunk in response_generator:
        chunk = chunk[0].content

        if chunk:
            message += chunk
            yield UpdateState(type="message", content=message)


async def chat(query: str, conversation_id: str, request_id: str, redis_repo):
    yield UpdateState(type="status", content="Started Response generation")
    sources_description = build_sources_description(conversation_id)
    tools = create_tools_for_request(request_id, redis_repo)
    
    mcp_manager = await MCPToolsManager.get_instance()
    await mcp_manager.ensure_initialized()
    mcp_tools = mcp_manager.get_tools()
    
    try:
        agent_generator = agent_response(
            query, sources_description, tools + mcp_tools)
        async for response in agent_generator:
            yield response
    except Exception as e:
        await mcp_manager.cleanup_resources()
        raise e
    finally:
        pass

    yield UpdateState(type="status", content="Finished Response generation")


async def shutdown_mcp_tools():
    mcp_manager = await MCPToolsManager.get_instance()
    await mcp_manager.cleanup_resources()
