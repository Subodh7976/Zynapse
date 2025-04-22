# Import AnyHttpUrl
from pydantic import BaseModel, Field, field_validator, AnyHttpUrl, ValidationInfo
from typing import Union, Optional, List
from datetime import datetime
from uuid import UUID

from .constants import SourceTypeEnum


class SourceInput(BaseModel):
    type: SourceTypeEnum = Field(..., description="The type of the source.")
    link: Optional[Union[AnyHttpUrl, str]] = Field(
        None, description="URL for YOUTUBE or WEB types.")
    file_identifier: Optional[str] = Field(
        None, description="Identifier (e.g., filename) for DOCUMENT type, must match an uploaded file's name.")
    title: Optional[str] = Field(
        None, max_length=512, description="Optional title for the source.")

    @field_validator('link')
    @classmethod
    def check_link_based_on_type(cls, v: Optional[Union[AnyHttpUrl, str]], info: ValidationInfo):
        # info.data contains the dictionary of fields already processed (or about to be if mode='before')
        source_type = info.data.get('type')
        if source_type in [SourceTypeEnum.YOUTUBE, SourceTypeEnum.WEB] and v is None:
            raise ValueError(
                f"A 'link' is required for source type '{source_type.value if source_type else 'unknown'}'")
        if source_type == SourceTypeEnum.DOCUMENT and v is not None:
            raise ValueError(
                f"'link' must be null for source type '{SourceTypeEnum.DOCUMENT.value}'")
        return v

    @field_validator('file_identifier')
    @classmethod
    def check_file_identifier_based_on_type(cls, v: Optional[str], info: ValidationInfo):
        source_type = info.data.get('type')
        if source_type == SourceTypeEnum.DOCUMENT and v is None:
            raise ValueError(
                f"A 'file_identifier' (matching an uploaded filename) is required for source type '{SourceTypeEnum.DOCUMENT.value}'")
        if source_type != SourceTypeEnum.DOCUMENT and v is not None:
            raise ValueError(
                f"'file_identifier' must be null for source types other than '{SourceTypeEnum.DOCUMENT.value}'")
        return v


class InitiateConversationRequest(BaseModel):
    title: str = Field(..., description="The title for the new conversation.")
    user_path: Optional[str] = Field(
        None, description="Optional user-defined path/category for these sources.")
    sources: List[SourceInput] = Field(
        ..., min_items=1, description="List of sources (documents, links) to associate with the conversation.")


class SourceResponse(BaseModel):
    id: UUID
    type: SourceTypeEnum
    title: str
    storage_reference: Optional[str] = None
    link: Optional[str] = None
    path: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime
    sources: List[SourceResponse] = []

    class Config:
        orm_mode = True
