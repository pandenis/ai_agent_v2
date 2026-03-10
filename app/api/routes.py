"""
API routes for AI Agent System with multi-model support
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_orchestrator
from app.services.orchestrator.orchestrator import IntelligentOrchestrator

from app.api.deps import get_agent_service, get_db, get_memory_service
from app.core.agent_config import TaskType
from app.schemas.agent import (
    AgentSelectionRequest,
    AgentSelectionResponse,
    AgentStatusResponse,
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentUpload,
    EnhancedChatRequest,
    EnhancedChatResponse,
    QueryAnalysisResponse,
    SessionCreate,
    SessionResponse,
    WebSearchRequest,
    WebSearchResponse,
    OrchestrateRequest,
    OrchestrateResponse,
    OrchestratorMetadata,
)
from app.schemas.memory import FactDeleteResponse, FactListRequest, FactListResponse, FactResponse, FactStatsResponse
from app.services.agent_service import AgentService
from app.services.document_service import DocumentService
from app.services.enhanced_chat_service import EnhancedChatService
from app.services.memory_service import MemoryService
from app.services.web_search_service import WebSearchService
from app.api.deps import get_write_gate
from app.schemas.memory_commands import MemoryWriteCommand
from app.services.memory_write_gate import MemoryWriteGate

# Security module import
from security.input_validation import SecurityValidator, validate_input

from app.schemas.modelfile import ModelCreateResponse, ModelDetail, ModelfileCreate, ModelList

router = APIRouter()


# ============================================================================
# MODELFILE ENDPOINTS
# ============================================================================


@router.get("/models", response_model=ModelList, summary="List available Ollama models")
async def get_models():
    from app.services.modelfile_service import ModelfileService
    result = await ModelfileService().list_models()
    return {"models": result}


@router.post("/models", response_model=ModelCreateResponse, status_code=status.HTTP_201_CREATED, summary="Create a model from Modelfile")
async def create_model(body: ModelfileCreate):
    from app.services.modelfile_service import ModelfileService
    return await ModelfileService().create_model(body.name, body.modelfile)


@router.get("/models/{name}", response_model=ModelDetail, summary="Get model info with Modelfile")
async def get_model(name: str):
    from app.services.modelfile_service import ModelfileService, ModelNotFoundError
    try:
        return await ModelfileService().get_model(name)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")


# ============================================================================
# NEW: AGENT MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/agents/status",
    response_model=AgentStatusResponse,
    summary="Get status of all AI agents",
    description="Returns availability and configuration of all registered agents",
)
async def get_agents_status(agent_service: AgentService = Depends(get_agent_service)):
    """Get comprehensive status of all AI agents"""
    status = await agent_service.get_agent_status()
    return status


@router.post(
    "/agents/select",
    response_model=AgentSelectionResponse,
    summary="Select best agent for task",
    description="Automatically select the most suitable agent for a given task",
)
async def select_best_agent(request: AgentSelectionRequest, agent_service: AgentService = Depends(get_agent_service)):
    """Intelligently select the best agent for a task"""

    # Security: Validate user input
    is_valid, sanitized_prompt, error = validate_input(request.prompt)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error}")

    # Parse task_type if provided
    task_type = None
    if request.task_type:
        try:
            task_type = TaskType(request.task_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task_type. Must be one of: {[t.value for t in TaskType]}",
            )

    # Select best agent
    selected_agent = await agent_service.select_best_agent_for_task(request.prompt, task_type=task_type)

    # Get agent config for details
    from app.core.agent_config import agent_registry

    config = agent_registry.get_agent_config(selected_agent)

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No suitable agent found")

    # Calculate confidence score
    confidence = 0.8
    if task_type:
        confidence = config.get_capability_score(task_type)

    return {
        "selected_agent": selected_agent,
        "confidence": confidence,
        "reasoning": f"Best match for {task_type.value if task_type else 'general task'}",
        "agent_capabilities": [{"name": c.name, "confidence": c.confidence} for c in config.capabilities],
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
async def create_session(session_data: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new chat session"""

    # Security: Validate agent name
    if session_data.agent_name:
        is_valid, sanitized_name, error = validate_input(session_data.agent_name)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent name: {error}"
            )
        session_data.agent_name = sanitized_name

    from app.models.session import Session

    # Generate UUID for session
    session = Session(
        session_id=str(uuid.uuid4()),  # ✅ FIX: Generate UUID
        agent_name=session_data.agent_name
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        session_id=session.session_id,  # ✅ FIX: Use session_id, not id
        agent_name=session.agent_name,
        created_at=session.created_at
    )


# ============================================================================
# SESSION HISTORY ENDPOINTS - NEW!
# ============================================================================


@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="Get all chat sessions",
    description="Returns list of all chat sessions ordered by last activity",
)
async def get_sessions(limit: int = 50, skip: int = 0, db: AsyncSession = Depends(get_db)):
    """Get list of all sessions with message counts (optimized single query)"""
    from app.models.session import Session
    from app.models.memory import ConversationMessage
    from sqlalchemy import func

    # BUG-05 FIX: Single query with LEFT JOIN and GROUP BY instead of N+1 queries
    stmt = (
        select(
            Session.session_id,
            Session.agent_name,
            Session.created_at,
            func.count(ConversationMessage.id).label("message_count")
        )
        .outerjoin(ConversationMessage, Session.session_id == ConversationMessage.session_id)
        .group_by(Session.session_id, Session.agent_name, Session.created_at)
        .order_by(desc(Session.created_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SessionResponse(
            session_id=row.session_id,
            agent_name=row.agent_name,
            created_at=row.created_at,
            message_count=row.message_count
        )
        for row in rows
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Returns details of a specific session",
)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get session by ID"""
    from app.models.session import Session

    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    return SessionResponse(session_id=session.session_id, agent_name=session.agent_name, created_at=session.created_at)


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Rename a session",
    description="Updates the session name/agent_name",
)
async def rename_session(session_id: str, update_data: dict, db: AsyncSession = Depends(get_db)):
    """Rename/update a session"""
    from app.models.session import Session
    
    # Check if session exists
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    
    # Update agent_name if provided
    if "agent_name" in update_data:
        new_name = update_data["agent_name"]
        if new_name:
            is_valid, sanitized_name, error = validate_input(new_name)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent name: {error}"
                )
            session.agent_name = sanitized_name
        else:
            session.agent_name = new_name
    
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=session.session_id,
        agent_name=session.agent_name,
        created_at=session.created_at,
        message_count=0  # TODO: count messages
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session",
    description="Deletes a session and all its messages",
)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete session and its messages"""
    from app.models.session import Session
    from app.models.memory import ConversationMessage
    
    # Check if session exists
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    
    # Delete messages first
    await db.execute(
        ConversationMessage.__table__.delete().where(
            ConversationMessage.session_id == session_id
        )
    )
    
    # Delete session
    await db.delete(session)
    await db.commit()
    
    return None


@router.get(
    "/sessions/{session_id}/messages",
    summary="Get session messages",
    description="Returns all messages from a session",
)
async def get_session_messages(session_id: str, limit: int = 100, skip: int = 0, db: AsyncSession = Depends(get_db)):
    """Get messages from session"""
    from app.models.memory import ConversationMessage
    from app.models.session import Session

    # Verify session exists
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    # Get messages
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.timestamp)
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "tokens_used": m.tokens_used,
            }
            for m in messages
        ],
        "total": len(messages),
    }


@router.get(
    "/sessions/{session_id}/facts",
    summary="Get facts extracted from session",
    description="Returns all facts extracted from this session",
)
async def get_session_facts(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get facts extracted from session"""
    from app.models.memory_v2 import FactModel
    from app.models.session import Session

    # Verify session exists
    result = await db.execute(select(Session).where(Session.session_id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")

    # Get facts from this session
    result = await db.execute(
        select(FactModel)
        .where(FactModel.source_session_id == session_id)
        .order_by(desc(FactModel.created))
    )
    facts = result.scalars().all()

    return {
        "session_id": session_id,
        "facts": [
            {
                "fact_id": f.fact_id,
                "text": f.text,
                "fact_type": f.fact_type,
                "importance": f.importance,
                "confidence": f.confidence,
                "created": f.created.isoformat(),
                "tags": f.tags or [],
            }
            for f in facts
        ],
        "total": len(facts),
    }


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================


@router.post(
    "/chat/enhanced",
    response_model=EnhancedChatResponse,
    summary="Enhanced chat with multi-source intelligence and agent selection",
)
async def enhanced_chat(
    request: EnhancedChatRequest,
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service),
    memory_service: MemoryService = Depends(get_memory_service),
    write_gate: MemoryWriteGate = Depends(get_write_gate),
):
    """Enhanced chat with multi-source intelligence and agent selection"""

    # Security: Validate user message (CRITICAL - main user input)
    is_valid, sanitized_message, error = validate_input(request.message)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid message: {error}")

    # Security: Validate session_id format
    is_valid_session, session_error = SecurityValidator.validate_session_id(request.session_id)
    if not is_valid_session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid session ID: {session_error}")

    document_service = DocumentService()
    web_search_service = WebSearchService()

    enhanced_service = EnhancedChatService(
        agent_service=agent_service,
        memory_service=memory_service,
        document_service=document_service,
        web_search_service=web_search_service,
        write_gate=write_gate,
    )

    result = await enhanced_service.process_message(
        session_id=request.session_id,
        message=request.message,
        agent_name=request.agent_name,
        include_memory=request.include_memory,
        db=db,
    )

    return EnhancedChatResponse(
        response=result["response"],
        session_id=request.session_id,
        agent_used=result.get("agent_used", "unknown"),
        sources_used=result.get("sources", []),
        tokens_used=result.get("tokens", 0),
        timestamp=result.get("timestamp"),
    )


@router.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index document",
)
async def upload_document(document: DocumentUpload):
    """Upload and index a document for semantic search"""

    # Security: Validate document text content
    is_valid, sanitized_text, error = validate_input(document.text)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid document content: {error}")

    # Security: Sanitize filename
    if document.filename:
        document.filename = SecurityValidator.sanitize_filename(document.filename)

    document_service = DocumentService()

    doc_id = await document_service.add_document(
        text=document.text, metadata={"filename": document.filename, "source": document.source}
    )

    return DocumentResponse(
        document_id=doc_id, filename=document.filename, message="Document uploaded and indexed successfully"
    )


@router.post("/documents/search", response_model=DocumentSearchResponse, summary="Search documents")
async def search_documents(request: DocumentSearchRequest):
    """Search indexed documents using semantic similarity"""
    document_service = DocumentService()

    results = await document_service.search_documents(query=request.query, n_results=request.n_results)

    return DocumentSearchResponse(results=results, total_found=len(results))


@router.post("/search/web", response_model=WebSearchResponse, summary="Web search")
async def web_search(request: WebSearchRequest):
    """Perform web search and get results"""

    # Security: Validate search query
    is_valid, sanitized_query, error = validate_input(request.query)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid search query: {error}")

    web_search_service = WebSearchService()

    results = await web_search_service.search(query=request.query, max_results=request.max_results)

    return WebSearchResponse(results=results, total_found=len(results))


# ============================================================================
# MEMORY/MEMORISATOR ENDPOINTS
# ============================================================================


@router.get(
    "/memory/facts",
    response_model=FactListResponse,
    summary="Get facts with filters",
    description="Retrieve facts with optional filtering by importance, type, and tags",
)
async def get_facts(
    min_importance: float = 0.5,
    fact_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    memory_service: MemoryService = Depends(get_memory_service),
    db: AsyncSession = Depends(get_db),
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
        offset=offset,
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
            needs_update=f.needs_update,
            subject=f.subject,
        )
        for f in facts
    ]

    return FactListResponse(facts=fact_responses, total=len(facts), limit=limit, offset=offset, has_more=has_more)


@router.get(
    "/memory/facts/{fact_id}",
    response_model=FactResponse,
    summary="Get a specific fact by ID",
    description="Retrieve a single fact by its unique identifier",
)
async def get_fact_by_id(
    fact_id: str, memory_service: MemoryService = Depends(get_memory_service), db: AsyncSession = Depends(get_db)
):
    """Get a specific fact by ID"""

    fact = await memory_service.get_fact_by_id(fact_id)

    if not fact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fact with ID {fact_id} not found")

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
        needs_update=fact.needs_update,
        subject=fact.subject,
    )


@router.delete(
    "/memory/facts/{fact_id}",
    response_model=FactDeleteResponse,
    summary="Delete a fact",
    description="Delete a fact by its ID",
)
async def delete_fact(
        fact_id: str,
        memory_service: MemoryService = Depends(get_memory_service),
        db: AsyncSession = Depends(get_db)
):
    """Delete a single fact by ID (uses MemoryService directly, not WriteGate)"""
    # First check if fact exists
    fact = await memory_service.get_fact_by_id(fact_id)
    if not fact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fact with ID {fact_id} not found")

    # Delete single fact directly (WriteGate is for bulk/thread operations)
    deleted = await memory_service.delete_fact(fact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to delete fact: {fact_id}")

    return FactDeleteResponse(success=True, fact_id=fact_id, message="Fact deleted successfully")


@router.get(
    "/memory/stats",
    response_model=FactStatsResponse,
    summary="Get memory statistics",
    description="Get statistics about stored facts",
)
async def get_memory_stats(memory_service: MemoryService = Depends(get_memory_service), db: AsyncSession = Depends(get_db)):
    """Get statistics about facts in memory"""

    stats = await memory_service.get_facts_stats()

    return FactStatsResponse(
        total_facts=stats["total_facts"], facts_by_type=stats["facts_by_type"], avg_importance=stats["avg_importance"]
    )


# ============================================================================
# ORCHESTRATOR ENDPOINT (NEW!)
# ============================================================================

@router.post(
    "/orchestrate",
    response_model=OrchestrateResponse,
    summary="Intelligent query orchestration",
    description="Process query through IntelligentOrchestrator with caching, circuit breaker, and analytics",
)
async def orchestrate_query(
        request: OrchestrateRequest,
        orchestrator: IntelligentOrchestrator = Depends(get_orchestrator),
        db: AsyncSession = Depends(get_db),
):
    """
    Intelligent query orchestration with all production features.
    """

    # Security: Validate query
    is_valid, sanitized_query, error = validate_input(request.query)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid query: {error}"
        )

    # Security: Validate session_id
    is_valid_session, session_error = SecurityValidator.validate_session_id(request.session_id)
    if not is_valid_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID: {session_error}"
        )

    # Process through orchestrator with error handling
    try:
        result = await orchestrator.process_query(
            query=sanitized_query,
            session_id=request.session_id,
            use_chains=request.use_chains,
        )
    except Exception as e:
        # Log error and return 500
        import logging
        logging.error(f"Orchestrator error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal processing error: {str(e)}"
        )

    # Save messages to database
    from app.models.memory import ConversationMessage
    from app.models.session import Session
    import json

    # Upsert session (create if not exists, so FK constraint is satisfied)
    existing = await db.execute(
        select(Session).where(Session.session_id == request.session_id)
    )
    if not existing.scalar_one_or_none():
        new_session = Session(
            session_id=request.session_id,
            agent_name="orchestrator",
        )
        db.add(new_session)
        await db.flush()  # flush but don't commit yet

    # Save user message
    user_msg = ConversationMessage(
        session_id=request.session_id,
        role="user",
        content=sanitized_query,
    )
    db.add(user_msg)

    # Save assistant message (ensure content is string)
    response_text = result.get("text", "")
    if not isinstance(response_text, str):
        response_text = json.dumps(response_text) if response_text else ""
    
    assistant_msg = ConversationMessage(
        session_id=request.session_id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)

    await db.commit()

    # Build response
    metadata = result.get("metadata", {})

    # Build query_analysis response if available
    query_analysis_data = result.get("query_analysis")
    query_analysis_response = None
    if query_analysis_data:
        query_analysis_response = QueryAnalysisResponse(
            complexity=query_analysis_data.get("complexity", "unknown"),
            intent=query_analysis_data.get("intent", "unknown"),
            topics=query_analysis_data.get("topics", []),
            entities=query_analysis_data.get("entities", []),
            query_type=query_analysis_data.get("query_type", "general"),
            confidence=query_analysis_data.get("confidence", 0.0)
        )

    return OrchestrateResponse(
        text=response_text,
        metadata=OrchestratorMetadata(
            strategy=metadata.get("strategy", "unknown"),
            confidence=metadata.get("confidence", 0.0),
            sources=metadata.get("sources", []),
            elapsed_time_ms=metadata.get("elapsed_time_ms", 0.0),
            cost_usd=metadata.get("cost_usd", 0.0),
            reasoning_depth=metadata.get("reasoning_depth", 0),
            cached=metadata.get("cached", False),
            memory_coverage=metadata.get("memory_coverage", 0.0),
        ),
        query_analysis=query_analysis_response,
        debug=result.get("debug") if request.include_debug else None,
    )

# ============================================================================
# System Stats Endpoints
# ============================================================================

@router.get(
    "/system/cache-stats",
    summary="Get cache statistics",
    description="Returns cache performance metrics including hits, misses, and hit rate",
)
async def get_cache_stats(
    orchestrator: IntelligentOrchestrator = Depends(get_orchestrator),
):
    """Get cache statistics from the shared response cache."""
    stats = orchestrator.response_cache.get_stats()
    return stats


@router.get(
    "/sessions/{session_id}/stats",
    summary="Get session statistics",
    description="Returns statistics for a specific session including message counts",
)
async def get_session_stats(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for a specific session."""
    from app.models.session import Session
    from app.models.memory import ConversationMessage
    
    # Check if session exists
    result = await db.execute(
        select(Session).where(Session.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Get message counts
    messages_result = await db.execute(
        select(ConversationMessage).where(ConversationMessage.session_id == session_id)
    )
    messages = messages_result.scalars().all()
    
    user_messages = sum(1 for m in messages if m.role == "user")
    assistant_messages = sum(1 for m in messages if m.role == "assistant")
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "agent_name": session.agent_name,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        
    }
