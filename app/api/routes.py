"""
API routes for AI Agent System with multi-model support
"""
from idlelib.query import Query

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_db, get_agent_service, get_memory_service
from app.schemas.agent import (
    SessionCreate,
    SessionResponse,
    EnhancedChatRequest,
    EnhancedChatResponse,
    DocumentUpload,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    WebSearchRequest,
    WebSearchResponse,
    AgentStatusResponse,
    AgentSelectionRequest,
    AgentSelectionResponse,
)
from app.services.agent_service import AgentService
from app.services.memory_service import MemoryService
from app.services.document_service import DocumentService
from app.services.web_search_service import WebSearchService
from app.services.enhanced_chat_service import EnhancedChatService
from app.core.agent_config import TaskType

router = APIRouter()


# ============================================================================
# NEW: AGENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get(
    "/agents/status",
    response_model=AgentStatusResponse,
    summary="Get status of all AI agents",
    description="Returns availability and configuration of all registered agents"
)
async def get_agents_status(
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get comprehensive status of all AI agents"""
    status = await agent_service.get_agent_status()
    return status


@router.post(
    "/agents/select",
    response_model=AgentSelectionResponse,
    summary="Select best agent for task",
    description="Automatically select the most suitable agent for a given task"
)
async def select_best_agent(
    request: AgentSelectionRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Intelligently select the best agent for a task"""
    # Parse task_type if provided
    task_type = None
    if request.task_type:
        try:
            task_type = TaskType(request.task_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task_type. Must be one of: {[t.value for t in TaskType]}"
            )
    
    # Select best agent
    selected_agent = await agent_service.select_best_agent_for_task(
        request.prompt,
        task_type=task_type
    )
    
    # Get agent config for details
    from app.core.agent_config import agent_registry
    config = agent_registry.get_agent_config(selected_agent)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable agent found"
        )
    
    # Calculate confidence score
    confidence = 0.8
    if task_type:
        confidence = config.get_capability_score(task_type)
    
    return {
        "selected_agent": selected_agent,
        "confidence": confidence,
        "reasoning": f"Best match for {task_type.value if task_type else 'general task'}",
        "agent_capabilities": [
            {"name": c.name, "confidence": c.confidence}
            for c in config.capabilities
        ]
    }


# ============================================================================
# EXISTING ENDPOINTS
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new chat session"
)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    from app.models.session import Session
    
    session = Session(agent_name=session_data.agent_name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=str(session.id),
        agent_name=session.agent_name,
        created_at=session.created_at
    )


@router.post(
    "/chat/enhanced",
    response_model=EnhancedChatResponse,
    summary="Enhanced chat with multi-source intelligence and agent selection"
)
async def enhanced_chat(
    request: EnhancedChatRequest,
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Enhanced chat with multi-source intelligence and agent selection"""
    document_service = DocumentService()
    web_search_service = WebSearchService()
    
    enhanced_service = EnhancedChatService(
        agent_service=agent_service,
        memory_service=memory_service,
        document_service=document_service,
        web_search_service=web_search_service
    )
    
    result = await enhanced_service.process_message(
        session_id=request.session_id,
        message=request.message,
        agent_name=request.agent_name,
        include_memory=request.include_memory,
        db=db
    )
    
    return EnhancedChatResponse(
        response=result["response"],
        session_id=request.session_id,
        agent_used=result.get("agent_used", "unknown"),
        sources_used=result.get("sources", []),
        tokens_used=result.get("tokens", 0),
        timestamp=result.get("timestamp")
    )


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index document"
)
async def upload_document(document: DocumentUpload):
    """Upload and index a document for semantic search"""
    document_service = DocumentService()
    
    doc_id = await document_service.add_document(
        text=document.text,
        metadata={
            "filename": document.filename,
            "source": document.source
        }
    )
    
    return DocumentResponse(
        document_id=doc_id,
        filename=document.filename,
        message="Document uploaded and indexed successfully"
    )


@router.post(
    "/documents/search",
    response_model=DocumentSearchResponse,
    summary="Search documents"
)
async def search_documents(request: DocumentSearchRequest):
    """Search indexed documents using semantic similarity"""
    document_service = DocumentService()
    
    results = await document_service.search_documents(
        query=request.query,
        n_results=request.n_results
    )
    
    return DocumentSearchResponse(
        results=results,
        total_found=len(results)
    )


@router.post(
    "/search/web",
    response_model=WebSearchResponse,
    summary="Web search"
)
async def web_search(request: WebSearchRequest):
    """Perform web search and get results"""
    web_search_service = WebSearchService()
    
    results = await web_search_service.search(
        query=request.query,
        max_results=request.max_results
    )
    
    return WebSearchResponse(
        results=results,
        total_found=len(results)
    )


# ============================================================================
# MEMORY/MEMORISATOR ENDPOINTS
# ============================================================================

from app.schemas.memory import (
    FactResponse,
    FactListRequest,
    FactListResponse,
    FactStatsResponse,
    FactDeleteResponse
)


@router.get(
    "/memory/facts",
    response_model=FactListResponse,
    summary="Get facts with filters",
    description="Retrieve facts with optional filtering by importance, type, and tags"
)
async def get_facts(
        min_importance: float = 0.5,
        fact_type: Optional[str] = None,
        tags: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        memory_service: MemoryService = Depends(get_memory_service),
        db: AsyncSession = Depends(get_db)
):
    """Get list of facts with filtering and pagination"""

    # Parse tags if provided
    tag_list = tags.split(",") if tags else None

    # Get facts from database (get limit+1 to check if more exist)
    facts = await memory_service.get_facts(
        min_importance=min_importance,
        fact_type=fact_type,
        tags=tag_list,
        limit=limit + 1,  # Get one extra to check has_more
        offset=offset
    )

    # Check if more facts available
    has_more = len(facts) > limit

    # Trim to requested limit
    if has_more:
        facts = facts[:limit]

    # Convert to response models
    fact_responses = [
        FactResponse(
            fact_id=f.fact_id,
            text=f.text,
            importance=f.importance,
            confidence=f.confidence,
            tags=f.tags or [],
            fact_type=f.fact_type,
            source=f.source,
            created=f.created,
            updated=f.updated,
            last_accessed=f.last_accessed,
            usage_count=f.usage_count,
            needs_update=f.needs_update
        )
        for f in facts
    ]

    return FactListResponse(
        facts=fact_responses,
        total=len(facts),
        limit=limit,
        offset=offset,
        has_more=has_more
    )


@router.get(
    "/memory/facts/{fact_id}",
    response_model=FactResponse,
    summary="Get a specific fact by ID",
    description="Retrieve a single fact by its unique identifier"
)
async def get_fact_by_id(
        fact_id: str,
        memory_service: MemoryService = Depends(get_memory_service),
        db: AsyncSession = Depends(get_db)
):
    """Get a specific fact by ID"""

    fact = await memory_service.get_fact_by_id(fact_id)

    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact with ID {fact_id} not found"
        )

    return FactResponse(
        fact_id=fact.fact_id,
        text=fact.text,
        importance=fact.importance,
        confidence=fact.confidence,
        tags=fact.tags or [],
        fact_type=fact.fact_type,
        source=fact.source,
        created=fact.created,
        updated=fact.updated,
        last_accessed=fact.last_accessed,
        usage_count=fact.usage_count,
        needs_update=fact.needs_update
    )


@router.delete(
    "/memory/facts/{fact_id}",
    response_model=FactDeleteResponse,
    summary="Delete a fact",
    description="Delete a fact by its ID"
)
async def delete_fact(
        fact_id: str,
        memory_service: MemoryService = Depends(get_memory_service),
        db: AsyncSession = Depends(get_db)
):
    """Delete a fact by ID"""

    success = await memory_service.delete_fact(fact_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact with ID {fact_id} not found"
        )

    return FactDeleteResponse(
        success=True,
        fact_id=fact_id,
        message="Fact deleted successfully"
    )


@router.get(
    "/memory/stats",
    response_model=FactStatsResponse,
    summary="Get memory statistics",
    description="Get statistics about stored facts"
)
async def get_memory_stats(
        memory_service: MemoryService = Depends(get_memory_service),
        db: AsyncSession = Depends(get_db)
):
    """Get statistics about facts in memory"""

    stats = await memory_service.get_facts_stats()

    return FactStatsResponse(
        total_facts=stats["total_facts"],
        facts_by_type=stats["facts_by_type"],
        avg_importance=stats["avg_importance"]
    )