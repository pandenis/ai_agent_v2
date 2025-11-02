"""
FastAPI dependencies
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.memory_service import MemoryService
from app.services.agent_service import AgentService
from app.services.document_service import DocumentService
from app.services.web_search_service import WebSearchService
from app.services.enhanced_chat_service import EnhancedChatService


async def get_memory_service(
    db: AsyncSession = Depends(get_db)
) -> MemoryService:
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
    web_search_service: WebSearchService = Depends(get_web_search_service)
) -> EnhancedChatService:
    """Dependency for enhanced chat service"""
    return EnhancedChatService(
        memory_service=memory_service,
        agent_service=agent_service,
        document_service=document_service,
        web_search_service=web_search_service
    )
