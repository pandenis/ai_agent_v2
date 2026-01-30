"""
Unit tests for MemoryCleanupService

Task 3.3: Implement MemoryCleanupService with expiration logic
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock


class TestMemoryCleanupServiceInit:
    """Test MemoryCleanupService initialization"""

    def test_cleanup_service_exists(self):
        """Test: MemoryCleanupService class exists"""
        from app.services.memory_cleanup_service import MemoryCleanupService

        assert MemoryCleanupService is not None

    def test_cleanup_service_requires_db_session(self):
        """Test: MemoryCleanupService requires db session"""
        from app.services.memory_cleanup_service import MemoryCleanupService

        mock_db = MagicMock()
        service = MemoryCleanupService(db=mock_db)

        assert service.db == mock_db