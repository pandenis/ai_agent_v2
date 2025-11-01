"""
FastAPI dependencies
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.memory_service import MemoryService
from app.services.agent_service import AgentService


async def get_memory_service(
    db: AsyncSession = Depends(get_db)
) -> MemoryService:
    """Dependency for memory service"""
    return MemoryService(db)


async def get_agent_service() -> AgentService:
    """Dependency for agent service"""
    return AgentService()
