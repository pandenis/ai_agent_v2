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
        self.is_running = False
        self._task = None

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

    def start(self, cleanup_service) -> None:
        """
        Start the background cleanup scheduler.

        Args:
            cleanup_service: MemoryCleanupService instance
        """
        self.is_running = True
        logger.info(f"Cleanup scheduler started (interval: {self.interval_seconds}s)")

    def stop(self) -> None:
        """
        Stop the background cleanup scheduler.
        """
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Cleanup scheduler stopped")

async def create_cleanup_task(
        cleanup_service,
        interval_seconds: int = 3600
) -> CleanupScheduler:
    """
    Create and start a cleanup scheduler task.

    Args:
        cleanup_service: MemoryCleanupService instance
        interval_seconds: Interval between cleanups

    Returns:
        Started CleanupScheduler instance
    """
    scheduler = CleanupScheduler(interval_seconds=interval_seconds)
    scheduler.start(cleanup_service)
    return scheduler