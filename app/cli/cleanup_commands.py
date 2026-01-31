"""
Cleanup CLI Commands for manual memory maintenance.

Task 3.5: Add cleanup CLI commands and admin endpoints

Provides command-line interface for:
- Viewing cleanup statistics
- Running manual cleanup
- Checking expired facts
"""

import asyncio
from typing import Optional


async def get_cleanup_stats(db_session) -> dict:
    """
    Get statistics about expired facts pending cleanup.

    Args:
        db_session: Database session

    Returns:
        Dict with cleanup statistics
    """
    from app.services.memory_cleanup_service import MemoryCleanupService

    cleanup_service = MemoryCleanupService(db=db_session)
    return await cleanup_service.get_cleanup_stats()