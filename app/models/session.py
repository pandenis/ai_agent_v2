"""
Session model for storing chat sessions
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Session(Base):
    """Chat session model"""
    __tablename__ = "sessions"
    
    # Primary key с auto-generate UUID
    session_id = Column(
        String, 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    user_id = Column(String, nullable=True)
    agent_name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Session(id={self.session_id}, agent={self.agent_name})>"
