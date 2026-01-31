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

class TestRunCleanup:
    """Test run_cleanup CLI function"""

    def test_run_cleanup_exists(self):
        """Test: run_cleanup function exists"""
        from app.cli.cleanup_commands import run_cleanup

        assert run_cleanup is not None
        assert callable(run_cleanup)

    @pytest.mark.asyncio
    async def test_run_cleanup_deletes_expired_facts(self):
        """Test: run_cleanup with dry_run=False actually deletes facts"""
        from app.cli.cleanup_commands import run_cleanup

        mock_db = MagicMock()

        with patch('app.services.memory_cleanup_service.MemoryCleanupService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.cleanup_expired_facts = AsyncMock(return_value=5)
            mock_service_class.return_value = mock_service

            result = await run_cleanup(mock_db, dry_run=False)

            assert result["dry_run"] is False
            assert result["deleted"] == 5
            mock_service.cleanup_expired_facts.assert_called_once()

@pytest.mark.asyncio
async def test_run_cleanup_dry_run_returns_stats(self):
    """Test: run_cleanup with dry_run=True returns stats without deleting"""
    from app.cli.cleanup_commands import run_cleanup

    mock_db = MagicMock()

    with patch('app.services.memory_cleanup_service.MemoryCleanupService') as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_cleanup_stats = AsyncMock(return_value={
            "total_expired": 10,
            "by_type": {"weather": 7, "event": 3}
        })
        mock_service.cleanup_expired_facts = AsyncMock(return_value=10)
        mock_service_class.return_value = mock_service

        result = await run_cleanup(mock_db, dry_run=True)

        assert result["dry_run"] is True
        assert result["would_delete"] == 10
        mock_service.cleanup_expired_facts.assert_not_called()

class TestCleanupAPIEndpoint:
    """Test cleanup API endpoint handler"""

    def test_cleanup_endpoint_handler_exists(self):
        """Test: cleanup_endpoint_handler function exists"""
        from app.cli.cleanup_commands import cleanup_endpoint_handler

        assert cleanup_endpoint_handler is not None
        assert callable(cleanup_endpoint_handler)