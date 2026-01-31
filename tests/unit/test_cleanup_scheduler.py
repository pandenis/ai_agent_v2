"""
Unit tests for Cleanup Scheduler

Task 3.4: Add scheduled cleanup task for expired facts
"""

import pytest
import asyncio
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

    @pytest.mark.asyncio
    async def test_run_cleanup_returns_zero_when_none_expired(self):
        """Test: run_cleanup returns 0 when no facts expired"""
        from app.services.cleanup_scheduler import CleanupScheduler

        # Arrange
        mock_cleanup_service = MagicMock()
        mock_cleanup_service.cleanup_expired_facts = AsyncMock(return_value=0)

        scheduler = CleanupScheduler()

        # Act
        result = await scheduler.run_cleanup(mock_cleanup_service)

        # Assert
        assert result == 0

class TestSchedulerStartStop:
    """Test scheduler start and stop functionality"""

    def test_scheduler_is_running_initially_false(self):
        """Test: Scheduler is not running after init"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler()

        assert scheduler.is_running is False

    def test_scheduler_has_start_method(self):
        """Test: Scheduler has start method"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler()

        assert hasattr(scheduler, 'start')
        assert callable(scheduler.start)

    def test_scheduler_has_stop_method(self):
        """Test: Scheduler has stop method"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler()

        assert hasattr(scheduler, 'stop')
        assert callable(scheduler.stop)

    def test_start_sets_is_running_true(self):
        """Test: start() sets is_running to True"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler()
        mock_cleanup_service = MagicMock()

        scheduler.start(mock_cleanup_service)

        assert scheduler.is_running is True

    def test_stop_sets_is_running_false(self):
        """Test: stop() sets is_running to False"""
        from app.services.cleanup_scheduler import CleanupScheduler

        scheduler = CleanupScheduler()
        mock_cleanup_service = MagicMock()

        scheduler.start(mock_cleanup_service)
        scheduler.stop()

        assert scheduler.is_running is False

class TestCreateCleanupTask:
    """Test create_cleanup_task factory function"""

    @pytest.mark.asyncio
    async def test_create_cleanup_task_exists(self):
        """Test: create_cleanup_task function exists"""
        from app.services.cleanup_scheduler import create_cleanup_task

        assert create_cleanup_task is not None
        assert callable(create_cleanup_task)

    @pytest.mark.asyncio
    async def test_create_cleanup_task_returns_running_scheduler(self):
        """Test: create_cleanup_task returns a running scheduler"""
        from app.services.cleanup_scheduler import create_cleanup_task

        mock_cleanup_service = MagicMock()

        scheduler = await create_cleanup_task(mock_cleanup_service, interval_seconds=60)

        assert scheduler.is_running is True
        assert scheduler.interval_seconds == 60

        # Cleanup
        scheduler.stop()