"""
Pydantic schemas for Memory/Memorisator API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FactResponse(BaseModel):
    """Response schema for a single fact"""

    fact_id: str = Field(..., description="Unique fact identifier")
    text: str = Field(..., description="Fact text content")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance score (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    tags: List[str] = Field(default_factory=list, description="Fact tags")
    fact_type: str = Field(..., description="Type: static, event, preference, knowledge, weather")
    source: str = Field(default="conversation", description="Source of fact")
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    last_accessed: Optional[datetime] = Field(None, description="Last accessed timestamp")
    usage_count: int = Field(default=0, description="Number of times fact was used")
    needs_update: bool = Field(default=False, description="Whether fact needs updating")
    subject: str = Field(default='user', description="Subject category of the fact")

    class Config:
        from_attributes = True


class FactListRequest(BaseModel):
    """Request parameters for listing facts"""

    min_importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum importance threshold")
    fact_type: Optional[str] = Field(None, description="Filter by fact type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (OR logic)")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of facts to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class FactListResponse(BaseModel):
    """Response schema for list of facts"""

    facts: List[FactResponse] = Field(..., description="List of facts")
    total: int = Field(..., description="Total number of facts matching filters")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")
    has_more: bool = Field(..., description="Whether more facts are available")


class FactStatsResponse(BaseModel):
    """Response schema for fact statistics"""

    total_facts: int = Field(..., description="Total number of facts")
    facts_by_type: Dict[str, int] = Field(..., description="Count of facts by type")
    avg_importance: float = Field(..., description="Average importance score")


class FactDeleteResponse(BaseModel):
    """Response schema for fact deletion"""

    success: bool = Field(..., description="Whether deletion was successful")
    fact_id: str = Field(..., description="ID of deleted fact")
    message: str = Field(..., description="Status message")


class ErrorResponse(BaseModel):
    """Error response schema"""

    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
