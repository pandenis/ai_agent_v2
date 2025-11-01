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


class DocumentUpload(BaseModel):
    """Request schema for document upload"""
    text: str = Field(..., description="Document text content")
    filename: Optional[str] = Field(None, description="Original filename")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class DocumentSearchRequest(BaseModel):
    """Request schema for document search"""
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)


class WebSearchRequest(BaseModel):
    """Request schema for web search"""
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=10)
