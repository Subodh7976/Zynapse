from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.core.constants import SUMMARIZER_MODEL
from .prompts import SUMMARIZER_PROMPT


class BriefSummary(BaseModel):
    brief: str = Field(
        description="short brief description, describing the content of the Source")
    summary: str = Field(
        description="Comprehensive summary of the source, describing the complete content of the source")


parser = JsonOutputParser(pydantic_object=BriefSummary)
llm = ChatGoogleGenerativeAI(model=SUMMARIZER_MODEL, temperature=0.7)
prompt = PromptTemplate(
    template=SUMMARIZER_PROMPT,
    input_variables=['document_type', 'content'],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
chain = prompt | llm | parser


async def get_brief_summary(document_type: str, content: str) -> dict:
    try:
        response = await chain.ainvoke({"document_type": document_type, "content": content})
    except:
        response = {}
    return response
