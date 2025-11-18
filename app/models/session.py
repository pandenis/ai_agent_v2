"""
Session model for managing conversation sessions
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Session identifier (UUID-like)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # User identifier (for future multi-user support)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Agent used in this session
    agent_name: Mapped[str] = mapped_column(String(50), default="mistral")

    # Session metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Statistics
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, session_id={self.session_id}, agent={self.agent_name})>"
