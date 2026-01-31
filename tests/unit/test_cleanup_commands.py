"""
Unit tests for Cleanup CLI Commands

Task 3.5: Add cleanup CLI commands and admin endpoints
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestGetCleanupStats:
    """Test get_cleanup_stats CLI function"""

    def test_get_cleanup_stats_exists(self):
        """Test: get_cleanup_stats function exists"""
        from app.cli.cleanup_commands import get_cleanup_stats

        assert get_cleanup_stats is not None
        assert callable(get_cleanup_stats)

    @pytest.mark.asyncio
    async def test_get_cleanup_stats_returns_stats(self):
        """Test: get_cleanup_stats returns cleanup statistics"""
        from app.cli.cleanup_commands import get_cleanup_stats

        mock_db = MagicMock()

        with patch('app.services.memory_cleanup_service.MemoryCleanupService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_cleanup_stats = AsyncMock(return_value={
                "total_expired": 5,
                "by_type": {"weather": 3, "event": 2}
            })
            mock_service_class.return_value = mock_service

            result = await get_cleanup_stats(mock_db)

            assert result["total_expired"] == 5
            assert result["by_type"]["weather"] == 3