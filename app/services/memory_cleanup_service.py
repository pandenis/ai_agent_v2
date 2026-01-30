"""
Memory Cleanup Service for expired fact management.

Task 3.3: Implement MemoryCleanupService with expiration logic

Provides functionality to find and delete expired facts based on
their expires_at timestamp.
"""

from sqlalchemy.ext.asyncio import AsyncSession


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