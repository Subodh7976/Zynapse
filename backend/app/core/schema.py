from fastapi import UploadFile
from pydantic import BaseModel
from typing import Any

from config import SourceTypeEnum


class InitiatePage(BaseModel):
    title: str


class UploadSource(BaseModel):
    source: UploadFile | str
    type: SourceTypeEnum
    conversation_id: str


class ChatRequest(BaseModel):
    query: str
    conversation_id: str


class UpdateState(BaseModel):
    type: str
    content: Any
