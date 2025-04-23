from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from app.config import CHAT_AGENT_MODEL
from app.helper.utils import build_sources_description
from app.core.schema import UpdateState
from .tools import create_tools_for_request
from .prompts import CHAT_AGENT_PROMPT

llm = ChatGoogleGenerativeAI(model=CHAT_AGENT_MODEL, temperature=0.7)
prompt = PromptTemplate(
    template=CHAT_AGENT_PROMPT,
    input_variables=['sources']
)


async def agent_response(query: str, sources: str, tools: list):
    agent = create_react_agent(
        llm, tools, prompt=prompt.format(sources=sources))
    response_generator = agent.astream(
        {"input": query}, stream_mode="messages")

    message = ""
    async for chunk in response_generator:
        chunk = chunk.content

        if chunk:
            message += chunk
            UpdateState(type="message", content=message)


async def chat(query: str, conversation_id: str, request_id: str, redis_repo):
    yield UpdateState(type="status", content="Started Response generation")
    sources_description = build_sources_description(conversation_id)
    tools = create_tools_for_request(request_id, redis_repo)

    agent_generator = agent_response(query, sources_description, tools)
    async for response in agent_generator:
        yield response

    yield UpdateState(type="status", content="Finished Response generation")
