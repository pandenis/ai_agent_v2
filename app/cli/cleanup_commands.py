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

async def run_cleanup(db_session, dry_run: bool = False) -> dict:
    """
    Run cleanup of expired facts.

    Args:
        db_session: Database session
        dry_run: If True, only report what would be deleted

    Returns:
        Dict with cleanup results
    """
    from app.services.memory_cleanup_service import MemoryCleanupService

    cleanup_service = MemoryCleanupService(db=db_session)

    if dry_run:
        stats = await cleanup_service.get_cleanup_stats()
        return {
            "dry_run": True,
            "would_delete": stats["total_expired"],
            "by_type": stats["by_type"]
        }

    deleted_count = await cleanup_service.cleanup_expired_facts()
    return {
        "dry_run": False,
        "deleted": deleted_count
    }


async def cleanup_endpoint_handler(db_session, dry_run: bool = True) -> dict:
    """
    API endpoint handler for cleanup operations.

    Args:
        db_session: Database session
        dry_run: If True, only report stats (default: True for safety)

    Returns:
        Dict with operation results
    """
    if dry_run:
        stats = await get_cleanup_stats(db_session)
        return {
            "action": "stats",
            "total_expired": stats["total_expired"],
            "by_type": stats["by_type"]
        }

    result = await run_cleanup(db_session, dry_run=False)
    return {
        "action": "cleanup",
        "deleted": result["deleted"]
    }