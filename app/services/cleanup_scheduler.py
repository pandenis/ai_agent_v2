"""
Cleanup Scheduler for automated expired fact removal.

Task 3.4: Add scheduled cleanup task

Provides a background scheduler that periodically runs
the MemoryCleanupService to remove expired facts.
"""

import logging

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """
    Scheduler for periodic cleanup of expired facts.

    Attributes:
        interval_seconds: Time between cleanup runs
    """

    def __init__(self, interval_seconds: int = 3600):
        """
        Initialize cleanup scheduler.

        Args:
            interval_seconds: Interval between cleanups (default: 1 hour)
        """
        self.interval_seconds = interval_seconds

    async def run_cleanup(self, cleanup_service) -> int:
        """
        Run a single cleanup cycle.

        Args:
            cleanup_service: MemoryCleanupService instance

        Returns:
            Number of facts deleted
        """
        deleted_count = await cleanup_service.cleanup_expired_facts()
        logger.info(f"Cleanup completed: {deleted_count} expired facts removed")
        return deleted_count