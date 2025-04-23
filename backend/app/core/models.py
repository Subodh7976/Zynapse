from sqlalchemy import (
    String, DateTime, 
    ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from backend.app.config import SourceTypeEnum

class Base(DeclarativeBase):
    pass


class Conversation(Base):
    """Represents a temporary conversation session."""
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )
    conversation_data: Mapped[Dict[str, Any]] = mapped_column(
        "conversation",
        JSONB,
        nullable=False,
        server_default='{}'
    )
    sources: Mapped[List["Source"]] = relationship(
        "Source", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', updated_at='{self.updated_at}')>"


class Source(Base):
    """Represents a source document/link associated with a temporary conversation."""
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[SourceTypeEnum] = mapped_column(
        SQLEnum(SourceTypeEnum, name="sourcetypeenum",
                create_type=True),  # Ensure enum type exists
        nullable=False,
        index=True,
    )
    link: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
        comment="Source URL. Used when type is YOUTUBE or WEB."
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Text content parsed from the source file or link."
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    brief: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="sources"
    )

    def __repr__(self):
        return f"<Source(id={self.id}, type='{self.type.value}', title='{self.title}')>"

