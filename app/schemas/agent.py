"""
Pydantic schemas for API requests and responses
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ============================================================================
# SESSION SCHEMAS
# ============================================================================


class SessionCreate(BaseModel):
    """Schema for creating a new session"""

    agent_name: str = Field(default="mistral", description="AI agent to use")


class SessionResponse(BaseModel):
    """Schema for session response"""

    session_id: str
    agent_name: str
    created_at: datetime
    message_count: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo else v.isoformat() + "Z"
        }
# ============================================================================
# CHAT SCHEMAS
# ============================================================================


class ChatRequest(BaseModel):
    """Basic chat request"""

    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Basic chat response"""

    response: str
    session_id: str


class EnhancedChatRequest(BaseModel):
    """Enhanced chat request with agent selection"""

    session_id: str
    message: str
    agent_name: Optional[str] = Field(None, description="Specific agent to use (leave empty for automatic selection)")
    include_memory: bool = True


class EnhancedChatResponse(BaseModel):
    """Enhanced chat response with agent info"""

    response: str
    session_id: str
    agent_used: str
    sources_used: List[str] = []
    tokens_used: int = 0
    timestamp: Optional[str] = None


# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================


class DocumentUpload(BaseModel):
    """Schema for uploading documents"""

    text: str = Field(..., description="Document text content")
    filename: str = Field(..., description="Document filename")
    source: str = Field(default="upload", description="Source of document")


class DocumentResponse(BaseModel):
    """Schema for document upload response"""

    document_id: str
    filename: str
    message: str


class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""

    query: str = Field(..., description="Search query")
    n_results: int = Field(default=5, description="Number of results to return")


class DocumentSearchResponse(BaseModel):
    """Schema for document search response"""

    results: List[Dict[str, Any]]
    total_found: int


# ============================================================================
# WEB SEARCH SCHEMAS
# ============================================================================


class WebSearchRequest(BaseModel):
    """Schema for web search request"""

    query: str = Field(..., description="Search query")
    max_results: int = Field(default=5, description="Maximum results")


class WebSearchResponse(BaseModel):
    """Schema for web search response"""

    results: List[Dict[str, Any]]
    total_found: int


# ============================================================================
# MULTI-MODEL AGENT SCHEMAS
# ============================================================================


class AgentInfo(BaseModel):
    """Information about a single agent"""

    enabled: bool
    available: bool
    type: str
    description: str
    capabilities: List[Dict[str, Any]]


class AgentStatusResponse(BaseModel):
    """Response for agent status endpoint"""

    agents: Dict[str, AgentInfo]
    default_agent: str
    total_agents: int
    enabled_agents: int
    available_agents: int


class AgentSelectionRequest(BaseModel):
    """Request for agent selection"""

    prompt: str = Field(..., description="User prompt to analyze")
    task_type: Optional[str] = Field(None, description="Explicit task type (general_chat, code_analysis, medical_query, etc.)")


class AgentCapabilityInfo(BaseModel):
    """Agent capability information"""

    name: str
    confidence: float


class AgentSelectionResponse(BaseModel):
    """Response for agent selection"""

    selected_agent: str
    confidence: float
    reasoning: str
    agent_capabilities: List[AgentCapabilityInfo]

# Pydantic models

class OrchestrateRequest(BaseModel):
    """Request for orchestrate endpoint"""
    query: str = Field(..., min_length=1, max_length=5000, description="User query")
    session_id: str = Field(..., min_length=1, max_length=100, description="Session ID")
    use_chains: bool = Field(default=False, description="Use chain execution mode")
    include_debug: bool = Field(default=False, description="Include debug info")


class OrchestratorMetadata(BaseModel):
    """Metadata from orchestrator response"""
    strategy: str
    confidence: float
    sources: List[str]
    elapsed_time_ms: float = Field(default=0.0)
    cost_usd: float = Field(default=0.0)
    reasoning_depth: int = Field(default=0)
    cached: bool = Field(default=False)
    memory_coverage: float = Field(default=0.0)


class OrchestrateResponse(BaseModel):
    """Response from orchestrate endpoint"""
    text: str
    metadata: OrchestratorMetadata
    debug: Optional[Dict[str, Any]] = None
