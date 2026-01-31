"""
Unit tests for Cleanup Scheduler

Task 3.4: Add scheduled cleanup task for expired facts
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestCleanupSchedulerInit:
    """Test CleanupScheduler initialization"""

    def test_cleanup_scheduler_exists(self):
        """Test: CleanupScheduler class exists"""
        from app.services.cleanup_scheduler import CleanupScheduler

        assert CleanupScheduler is not None

    def test_cleanup_scheduler_has_interval_seconds(self):
        """Test: CleanupScheduler accepts interval_seconds parameter"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler(interval_seconds=3600)

        assert scheduler.interval_seconds == 3600

    def test_cleanup_scheduler_default_interval_one_hour(self):
        """Test: Default interval is 3600 seconds (1 hour)"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler()

        assert scheduler.interval_seconds == 3600

class TestRunCleanup:
    """Test run_cleanup method"""

    @pytest.mark.asyncio
    async def test_run_cleanup_calls_cleanup_service(self):
        """Test: run_cleanup executes MemoryCleanupService.cleanup_expired_facts"""
        from app.services.cleanup_scheduler import CleanupScheduler

        # Arrange
        mock_cleanup_service = MagicMock()
        mock_cleanup_service.cleanup_expired_facts = AsyncMock(return_value=5)

        scheduler = CleanupScheduler()

        # Act
        result = await scheduler.run_cleanup(mock_cleanup_service)

        # Assert
        mock_cleanup_service.cleanup_expired_facts.assert_called_once()
        assert result == 5