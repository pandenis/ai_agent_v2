"""
FastAPI dependencies - Updated with get_orchestrator

This module provides dependency injection for FastAPI routes.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.agent_config import agent_registry
from app.services.agent_service import AgentService
from app.services.document_service import DocumentService
from app.services.enhanced_chat_service import EnhancedChatService
from app.services.memory_service import MemoryService
from app.services.web_search_service import WebSearchService
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


async def get_memory_service(db: AsyncSession = Depends(get_db)) -> MemoryService:
    """Dependency for memory service"""
    return MemoryService(db)


async def get_agent_service() -> AgentService:
    """Dependency for agent service"""
    return AgentService()


async def get_document_service() -> DocumentService:
    """Dependency for document service"""
    return DocumentService()


async def get_web_search_service() -> WebSearchService:
    """Dependency for web search service"""
    return WebSearchService()


async def get_enhanced_chat_service(
    memory_service: MemoryService = Depends(get_memory_service),
    agent_service: AgentService = Depends(get_agent_service),
    document_service: DocumentService = Depends(get_document_service),
    web_search_service: WebSearchService = Depends(get_web_search_service),
) -> EnhancedChatService:
    """Dependency for enhanced chat service"""
    return EnhancedChatService(
        memory_service=memory_service,
        agent_service=agent_service,
        document_service=document_service,
        web_search_service=web_search_service,
    )


# ============================================================================
# NEW: Orchestrator Dependency
# ============================================================================

async def get_orchestrator(
    db: AsyncSession = Depends(get_db),
) -> IntelligentOrchestrator:
    """
    Dependency for IntelligentOrchestrator.

    Creates a fully configured orchestrator with all required services:
    - MemoryService for fact storage/retrieval
    - AgentRegistry for AI model access
    - WebSearchService for external information

    The orchestrator provides:
    - Response caching
    - Circuit breaker for fault tolerance
    - Rate limiting
    - A/B testing support
    - Analytics and metrics

    Usage in routes:
        @router.post("/api/v1/orchestrate")
        async def orchestrate(
            request: OrchestrateRequest,
            orchestrator: IntelligentOrchestrator = Depends(get_orchestrator)
        ):
            return await orchestrator.process_query(...)
    """
    # Create required services
    memory_service = MemoryService(db)
    web_search_service = WebSearchService()

    # Create orchestrator with all services
    orchestrator = IntelligentOrchestrator(
        memory_service=memory_service,
        agent_registry=agent_registry,  # Global registry from agent_config
        web_search_service=web_search_service,
        # fact_extractor and response_cache will use defaults
    )

    return orchestrator