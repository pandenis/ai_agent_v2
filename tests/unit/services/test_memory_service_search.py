# tests/unit/services/test_memory_service_search.py
"""
Task 36: Test MemoryService.search_facts with proper API
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from app.services.memory_service import MemoryService


class TestMemoryServiceSearch:
    """Tests for MemoryService.search_facts API."""

    @pytest.mark.asyncio
    async def test_search_facts_with_limit(self):
        """search_facts should accept limit parameter."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        ms = MemoryService(mock_db)

        # Should not raise TypeError
        result = await ms.search_facts(query="name", limit=10)

        assert result == []

    @pytest.mark.asyncio
    async def test_search_facts_returns_list(self):
        """search_facts should return list of facts."""
        mock_db = AsyncMock()

        # Create mock fact
        mock_fact = Mock()
        mock_fact.text = "User's name is Denis"
        mock_fact.importance = 0.9
        mock_fact.confidence = 0.95

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_fact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        ms = MemoryService(mock_db)
        result = await ms.search_facts(query="name")

        assert len(result) == 1
        assert result[0].text == "User's name is Denis"