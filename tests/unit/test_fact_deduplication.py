"""
TDD Tests for Fact Deduplication Prevention
Tests verify that add_facts() does NOT create duplicates
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.services.memory_service import MemoryService
from app.services.fact_extractor import Fact


class TestFactDeduplicationPrevention:
    """Tests for preventing duplicate facts at creation time"""

    @pytest.mark.asyncio
    async def test_add_facts_skips_exact_duplicate(self):
        """Test: Exact duplicate fact is not added"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = MemoryService(mock_db)

        # Mock existing facts in DB
        existing_fact = MagicMock()
        existing_fact.text = "User's name is Denis"
        existing_fact.fact_id = "existing-123"

        # Correct async mock chain
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [existing_fact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Try to add duplicate
        new_fact = Fact(
            fact_id="new-456",
            text="User's name is Denis",  # Exact same text
            importance=0.9,
            confidence=0.95,
            tags=["name"],
            created=datetime.utcnow(),
            updated=datetime.utcnow(),
        )

        result = await service.add_facts([new_fact])

        # Should not add (duplicate detected)
        assert len(result) == 0
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_facts_skips_similar_fact(self):
        """Test: Similar fact (>70% match) is not added"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = MemoryService(mock_db)

        # Mock existing facts
        existing_fact = MagicMock()
        existing_fact.text = "User's name is Denis"
        existing_fact.fact_id = "existing-123"

        # Correct async mock chain
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [existing_fact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Try to add similar (but not exact) fact
        new_fact = Fact(
            fact_id="new-456",
            text="The user's name is Denis.",  # Similar but not exact
            importance=0.9,
            confidence=0.95,
            tags=["name"],
            created=datetime.utcnow(),
            updated=datetime.utcnow(),
        )

        result = await service.add_facts([new_fact])

        # Should not add (similar detected)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_add_facts_allows_different_fact(self):
        """Test: Different fact is added normally"""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = MemoryService(mock_db)

        # Mock existing facts
        existing_fact = MagicMock()
        existing_fact.text = "User's name is Denis"
        existing_fact.fact_id = "existing-123"

        # Correct async mock chain
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [existing_fact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Add completely different fact
        new_fact = Fact(
            fact_id="new-456",
            text="User works as QA Engineer",  # Different topic
            importance=0.8,
            confidence=0.9,
            tags=["job"],
            created=datetime.utcnow(),
            updated=datetime.utcnow(),
        )

        result = await service.add_facts([new_fact])

        # Should add (different fact)
        assert mock_db.add.called