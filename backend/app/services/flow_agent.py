from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from app.config import FLOW_MODEL
from .prompts import FLOW_PROMPT


prompt = PromptTemplate(
    template=FLOW_PROMPT,
    input_variables=['context', 'instructions']
)
llm = ChatGoogleGenerativeAI(model=FLOW_MODEL, temperature=0)
chain = prompt | llm


async def generate_flow(context: str, instructions: str):
    try:
        response = await chain.ainvoke({"context": context, "instructions": instructions})
        response = response.content
    except Exception as e:
        print("Exception in Mind Map - ", e)
        response = {}
    return response
