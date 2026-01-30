"""
Memory Cleanup Service for expired fact management.

Task 3.3: Implement MemoryCleanupService with expiration logic

Provides functionality to find and delete expired facts based on
their expires_at timestamp.
"""

from datetime import datetime
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.memory_v2 import FactModel


class MemoryCleanupService:
    """
    Service for cleaning up expired facts from memory.

    Attributes:
        db: AsyncSession for database operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize cleanup service.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def get_expired_facts(self) -> List[FactModel]:
        """
        Get all facts that have expired.

        Returns:
            List of expired FactModel objects
        """
        now = datetime.utcnow()

        result = await self.db.execute(
            select(FactModel).where(
                FactModel.expires_at.isnot(None),
                FactModel.expires_at < now
            )
        )

        return list(result.scalars().all())

    async def cleanup_expired_facts(self) -> int:
        """
        Delete all expired facts from database.

        Returns:
            Number of facts deleted
        """
        expired_facts = await self.get_expired_facts()

        for fact in expired_facts:
            await self.db.delete(fact)

        await self.db.commit()

        return len(expired_facts)