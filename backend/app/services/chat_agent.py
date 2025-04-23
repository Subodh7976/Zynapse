from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate


from backend.app.config import CHAT_AGENT_MODEL
from .prompts import CHAT_AGENT_PROMPT

tools = []
llm = ChatGoogleGenerativeAI(model=CHAT_AGENT_MODEL, temperature=0.7)
prompt = PromptTemplate(
    template=CHAT_AGENT_PROMPT,
    input_variables=['sources']
)


async def agent_response(query: str, sources: str):
    agent = create_react_agent(
        llm, tools, prompt=prompt.format(sources=sources))
    response_generator = agent.astream(
        {"input": query}, stream_mode="messages")

    async for chunk in response_generator:
        pass


async def chat(query: str, conversation_id: str):
    pass
