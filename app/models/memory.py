"""
Memory model for storing conversation history and facts
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ConversationMessage(Base):
    """Individual conversation messages"""
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)

    # Message content
    role: Mapped[str] = mapped_column(String(20))  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)

    # Metadata
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session={self.session_id})>"


class UserFact(Base):
    """User facts extracted from conversations (Memorisator data)"""
    __tablename__ = "user_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Fact content
    text: Mapped[str] = mapped_column(Text)

    # Memorisator fields
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    tags: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Store as JSON array

    # Metadata
    source: Mapped[str] = mapped_column(String(50), default="conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    related_fact_ids: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<UserFact(id={self.id}, importance={self.importance}, text={self.text[:50]}...)>"