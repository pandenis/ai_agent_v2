"""
FastAPI routes for agent API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_memory_service, get_agent_service
from app.schemas.agent import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionResponse
)
from app.services.memory_service import MemoryService
from app.services.agent_service import AgentService
from app.models.session import Session
from datetime import datetime
import uuid


router = APIRouter(prefix="/api/v1", tags=["agent"])


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation session"""
    session = Session(
        session_id=str(uuid.uuid4()),
        agent_name=request.agent_name,
        user_id=request.user_id
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session information"""
    result = await db.execute(
        select(Session).where(Session.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    memory_service: MemoryService = Depends(get_memory_service),
    agent_service: AgentService = Depends(get_agent_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Process chat message and generate response
    
    This endpoint:
    1. Validates the session exists
    2. Retrieves conversation history and user facts
    3. Generates AI response
    4. Saves both user message and AI response to memory
    5. Returns the AI response
    """
    # Check session exists
    result = await db.execute(
        select(Session).where(Session.session_id == request.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get conversation context if requested
    conversation_history = []
    system_context = "You are a helpful AI assistant."
    
    if request.include_memory:
        # Get recent conversation
        recent_messages = await memory_service.get_conversation_history(
            request.session_id,
            limit=5
        )
        
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]
        
        # Get important facts
        important_facts = await memory_service.get_important_facts(
            min_importance=0.7,
            limit=5
        )
        
        if important_facts:
            facts_text = "\n".join([f"- {f.text}" for f in important_facts])
            system_context += f"\n\nKnown facts about the user:\n{facts_text}"
    
    # Generate AI response
    ai_result = await agent_service.generate_response(
        prompt=request.message,
        system_prompt=system_context,
        conversation_history=conversation_history
    )
    
    if ai_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ai_result["error"]
        )
    
    # Save user message
    await memory_service.add_message(
        session_id=request.session_id,
        role="user",
        content=request.message
    )
    
    # Save AI response
    await memory_service.add_message(
        session_id=request.session_id,
        role="assistant",
        content=ai_result["response"],
        tokens_used=ai_result.get("tokens")
    )
    
    # Update session stats
    session.message_count += 2
    session.last_activity = datetime.utcnow()
    await db.commit()
    
    return ChatResponse(
        response=ai_result["response"],
        session_id=request.session_id,
        tokens_used=ai_result.get("tokens"),
        timestamp=datetime.utcnow()
    )


@router.get("/health")
async def health_check(
    agent_service: AgentService = Depends(get_agent_service)
):
    """Health check endpoint"""
    ollama_status = await agent_service.check_health()
    
    return {
        "status": "healthy" if ollama_status else "degraded",
        "ollama": "connected" if ollama_status else "unavailable",
        "timestamp": datetime.utcnow()
    }


from app.services.document_service import DocumentService
from app.services.web_search_service import WebSearchService
from app.api.deps import get_document_service, get_web_search_service
from app.schemas.agent import DocumentUpload, DocumentSearchRequest, WebSearchRequest


@router.post("/documents/upload")
async def upload_document(
    request: DocumentUpload,
    doc_service: DocumentService = Depends(get_document_service)
):
    """Upload and index a document"""
    import uuid
    
    # Generate doc ID
    doc_id = str(uuid.uuid4())
    
    # Add metadata
    metadata = request.metadata or {}
    if request.filename:
        metadata["filename"] = request.filename
    
    # Add to vector store
    await doc_service.add_document(
        doc_id=doc_id,
        text=request.text,
        metadata=metadata
    )
    
    return {
        "doc_id": doc_id,
        "filename": request.filename,
        "status": "indexed",
        "text_length": len(request.text)
    }


@router.post("/documents/search")
async def search_documents(
    request: DocumentSearchRequest,
    doc_service: DocumentService = Depends(get_document_service)
):
    """Search documents by semantic similarity"""
    results = await doc_service.search_documents(
        request.query,
        request.max_results
    )
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }


@router.get("/documents/count")
async def get_document_count(
    doc_service: DocumentService = Depends(get_document_service)
):
    """Get total document count"""
    count = await doc_service.get_document_count()
    return {"count": count}


@router.post("/search/web")
async def web_search(
    request: WebSearchRequest,
    web_service: WebSearchService = Depends(get_web_search_service)
):
    """Search the web"""
    results = await web_service.search(
        request.query,
        request.max_results
    )
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }
