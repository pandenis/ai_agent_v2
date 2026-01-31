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