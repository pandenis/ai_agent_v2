"""
Test for MemoryService.update_fact method
Task 39: Required for deduplication merge
"""

import pytest
from app.services.memory_service import MemoryService
from app.models.memory_v2 import Fact, FactModel


class TestMemoryServiceUpdateFact:
    """Tests for MemoryService.update_fact method"""

    @pytest.mark.asyncio
    async def test_update_fact_tags(self, test_db):
        """Test: Update fact tags"""
        # Arrange
        memory_service = MemoryService(test_db)

        # Add a fact first
        fact = Fact(
            fact_id="test-update-1",
            text="User's name is Denis",
            importance=0.9,
            tags=["name"],
            usage_count=5,
        )
        await memory_service.add_facts([fact])

        # Act
        result = await memory_service.update_fact(
            fact_id="test-update-1",
            tags=["name", "personal", "identity"]
        )

        # Assert
        assert result is True
        updated = await memory_service.get_fact_by_id("test-update-1")
        assert set(updated.tags) == {"name", "personal", "identity"}

    @pytest.mark.asyncio
    async def test_update_fact_usage_count(self, test_db):
        """Test: Update fact usage_count"""
        # Arrange
        memory_service = MemoryService(test_db)

        fact = Fact(
            fact_id="test-update-2",
            text="User lives in Tel Aviv",
            importance=0.8,
            tags=["location"],
            usage_count=3,
        )
        await memory_service.add_facts([fact])

        # Act
        result = await memory_service.update_fact(
            fact_id="test-update-2",
            usage_count=10
        )

        # Assert
        assert result is True
        updated = await memory_service.get_fact_by_id("test-update-2")
        assert updated.usage_count == 10

    @pytest.mark.asyncio
    async def test_update_fact_multiple_fields(self, test_db):
        """Test: Update multiple fields at once"""
        # Arrange
        memory_service = MemoryService(test_db)

        fact = Fact(
            fact_id="test-update-3",
            text="User prefers Python",
            importance=0.7,
            tags=["programming"],
            usage_count=2,
        )
        await memory_service.add_facts([fact])

        # Act
        result = await memory_service.update_fact(
            fact_id="test-update-3",
            tags=["programming", "python", "preference"],
            usage_count=8,
            importance=0.85
        )

        # Assert
        assert result is True
        updated = await memory_service.get_fact_by_id("test-update-3")
        assert set(updated.tags) == {"programming", "python", "preference"}
        assert updated.usage_count == 8
        assert updated.importance == 0.85

    @pytest.mark.asyncio
    async def test_update_fact_not_found(self, test_db):
        """Test: Return False when fact not found"""
        # Arrange
        memory_service = MemoryService(test_db)

        # Act
        result = await memory_service.update_fact(
            fact_id="non-existent-fact",
            tags=["test"]
        )

        # Assert
        assert result is False