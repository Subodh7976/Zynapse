from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List

from config import MIND_MAP_MODEL
from .prompts import MIND_MAP_PROMPT


class Node(BaseModel):
    id: str
    label: str
    children: List['Node'] = Field(default=[])


parser = PydanticOutputParser(pydantic_object=Node)
prompt = PromptTemplate(
    template=MIND_MAP_PROMPT,
    input_variables=['context'],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
llm = ChatGoogleGenerativeAI(model=MIND_MAP_MODEL, temperature=0)
chain = prompt | llm | parser


async def generate_map(context: str):
    try:
        response = await chain.ainvoke({"context": context})
    except Exception as e:
        print("Exception in Mind Map - ", e)
        response = None
    return response
