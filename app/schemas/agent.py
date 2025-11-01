"""
Pydantic schemas for agent API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., min_length=1, max_length=3500)
    include_memory: bool = Field(default=True, description="Include memory context")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    response: str
    session_id: str
    tokens_used: Optional[int] = None
    timestamp: datetime


class SessionCreate(BaseModel):
    """Request schema for creating a new session"""
    agent_name: str = Field(default="mistral", description="Agent to use")
    user_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Response schema for session"""
    session_id: str
    agent_name: str
    created_at: datetime
    is_active: bool
    message_count: int
    
    class Config:
        from_attributes = True  # Enable ORM mode
