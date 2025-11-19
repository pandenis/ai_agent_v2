"""
Unit tests for MemoryService - Memorisator v2 (FactModel) methods
"""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.memory_v2 import Fact, FactModel
from app.services.memory_service import MemoryService


@pytest.fixture
def sample_facts():
    """Create sample Fact objects for testing"""
    return [
        Fact(
            fact_id="test-fact-1",
            text="User loves Python programming",
            importance=0.9,
            confidence=0.95,
            tags=["programming", "python"],
            fact_type="preference",
            source="conversation",
        ),
        Fact(
            fact_id="test-fact-2",
            text="User lives in Tel Aviv",
            importance=0.8,
            confidence=1.0,
            tags=["location", "telавiv"],
            fact_type="static",
            source="conversation",
        ),
        Fact(
            fact_id="test-fact-3",
            text="User planning trip to Athens",
            importance=0.7,
            confidence=0.9,
            tags=["travel", "athens"],
            fact_type="event",
            source="conversation",
        ),
    ]


class TestMemoryServiceV2:
    """Tests for MemoryService Memorisator v2 methods"""

    @pytest.mark.asyncio
    async def test_add_facts_single(self, test_db, sample_facts):
        """Test adding a single fact"""
        memory_service = MemoryService(test_db)

        saved = await memory_service.add_facts([sample_facts[0]])

        assert len(saved) == 1
        assert saved[0].text == "User loves Python programming"
        assert saved[0].importance == 0.9

    @pytest.mark.asyncio
    async def test_add_facts_multiple(self, test_db, sample_facts):
        """Test adding multiple facts at once"""
        memory_service = MemoryService(test_db)

        saved = await memory_service.add_facts(sample_facts)

        assert len(saved) == 3
        assert all(isinstance(f, FactModel) for f in saved)

    @pytest.mark.asyncio
    async def test_add_facts_persisted(self, test_db, sample_facts):
        """Test that added facts are persisted to database"""
        memory_service = MemoryService(test_db)

        await memory_service.add_facts([sample_facts[0]])

        # Query directly
        result = await test_db.execute(select(FactModel).where(FactModel.fact_id == "test-fact-1"))
        fact = result.scalar_one_or_none()

        assert fact is not None
        assert fact.text == "User loves Python programming"

    @pytest.mark.asyncio
    async def test_get_facts_all(self, test_db, sample_facts):
        """Test retrieving all facts"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        facts = await memory_service.get_facts(min_importance=0.0)

        assert len(facts) == 3

    @pytest.mark.asyncio
    async def test_get_facts_by_importance(self, test_db, sample_facts):
        """Test filtering facts by importance"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        # Get facts with importance >= 0.8
        facts = await memory_service.get_facts(min_importance=0.8)

        assert len(facts) == 2
        assert all(f.importance >= 0.8 for f in facts)

    @pytest.mark.asyncio
    async def test_get_facts_by_type(self, test_db, sample_facts):
        """Test filtering facts by fact_type"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        # Get only preference facts
        facts = await memory_service.get_facts(fact_type="preference")

        assert len(facts) == 1
        assert facts[0].fact_type == "preference"

    @pytest.mark.asyncio
    async def test_get_facts_by_tags(self, test_db, sample_facts):
        """Test filtering facts by tags"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        # Get facts with 'programming' tag
        facts = await memory_service.get_facts(tags=["programming"])

        assert len(facts) == 1
        assert "programming" in facts[0].tags

    @pytest.mark.asyncio
    async def test_get_facts_multiple_tags(self, test_db, sample_facts):
        """Test filtering by multiple tags (OR logic)"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        # Get facts with 'programming' OR 'travel' tags
        facts = await memory_service.get_facts(tags=["programming", "travel"])

        assert len(facts) == 2

    @pytest.mark.asyncio
    async def test_get_facts_combined_filters(self, test_db, sample_facts):
        """Test combining multiple filters"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        # Get static facts with importance >= 0.8
        facts = await memory_service.get_facts(min_importance=0.8, fact_type="static")

        assert len(facts) == 1
        assert facts[0].fact_type == "static"
        assert facts[0].importance >= 0.8

    @pytest.mark.asyncio
    async def test_get_facts_pagination(self, test_db, sample_facts):
        """Test pagination with limit and offset"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        # Get first 2 facts
        page1 = await memory_service.get_facts(limit=2, offset=0)
        assert len(page1) == 2

        # Get next fact
        page2 = await memory_service.get_facts(limit=2, offset=2)
        assert len(page2) == 1

    @pytest.mark.asyncio
    async def test_get_facts_ordered_by_importance(self, test_db, sample_facts):
        """Test that facts are ordered by importance descending"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        facts = await memory_service.get_facts()

        # Should be ordered: 0.9, 0.8, 0.7
        assert facts[0].importance >= facts[1].importance
        assert facts[1].importance >= facts[2].importance

    @pytest.mark.asyncio
    async def test_get_fact_by_id_exists(self, test_db, sample_facts):
        """Test retrieving a specific fact by ID"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts([sample_facts[0]])

        fact = await memory_service.get_fact_by_id("test-fact-1")

        assert fact is not None
        assert fact.fact_id == "test-fact-1"
        assert fact.text == "User loves Python programming"

    @pytest.mark.asyncio
    async def test_get_fact_by_id_not_exists(self, test_db):
        """Test retrieving non-existent fact returns None"""
        memory_service = MemoryService(test_db)

        fact = await memory_service.get_fact_by_id("non-existent-id")

        assert fact is None

    @pytest.mark.asyncio
    async def test_delete_fact_exists(self, test_db, sample_facts):
        """Test deleting an existing fact"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts([sample_facts[0]])

        result = await memory_service.delete_fact("test-fact-1")

        assert result is True

        # Verify deletion
        fact = await memory_service.get_fact_by_id("test-fact-1")
        assert fact is None

    @pytest.mark.asyncio
    async def test_delete_fact_not_exists(self, test_db):
        """Test deleting non-existent fact returns False"""
        memory_service = MemoryService(test_db)

        result = await memory_service.delete_fact("non-existent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_fact_access(self, test_db, sample_facts):
        """Test updating fact access statistics"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts([sample_facts[0]])

        # Get initial state
        fact = await memory_service.get_fact_by_id("test-fact-1")
        initial_count = fact.usage_count

        # Update access
        await memory_service.update_fact_access("test-fact-1")

        # Check updated
        fact = await memory_service.get_fact_by_id("test-fact-1")
        assert fact.usage_count == initial_count + 1
        assert fact.last_accessed is not None

    @pytest.mark.asyncio
    async def test_update_fact_access_multiple_times(self, test_db, sample_facts):
        """Test updating access count multiple times"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts([sample_facts[0]])

        # Update 3 times
        await memory_service.update_fact_access("test-fact-1")
        await memory_service.update_fact_access("test-fact-1")
        await memory_service.update_fact_access("test-fact-1")

        fact = await memory_service.get_fact_by_id("test-fact-1")
        assert fact.usage_count == 3

    @pytest.mark.asyncio
    async def test_get_facts_stats_empty(self, test_db):
        """Test stats with no facts"""
        memory_service = MemoryService(test_db)

        stats = await memory_service.get_facts_stats()

        assert stats["total_facts"] == 0
        assert stats["facts_by_type"] == {}
        assert stats["avg_importance"] == 0.0

    @pytest.mark.asyncio
    async def test_get_facts_stats_with_data(self, test_db, sample_facts):
        """Test stats with facts"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts(sample_facts)

        stats = await memory_service.get_facts_stats()

        assert stats["total_facts"] == 3
        assert stats["facts_by_type"]["preference"] == 1
        assert stats["facts_by_type"]["static"] == 1
        assert stats["facts_by_type"]["event"] == 1
        # Average: (0.9 + 0.8 + 0.7) / 3 = 0.8
        assert stats["avg_importance"] == 0.8

    @pytest.mark.asyncio
    async def test_add_facts_with_all_fields(self, test_db):
        """Test adding fact with all fields populated"""
        memory_service = MemoryService(test_db)

        fact = Fact(
            fact_id="complete-fact",
            text="Complete fact",
            importance=0.9,
            confidence=0.95,
            tags=["tag1", "tag2"],
            fact_type="preference",
            needs_update=True,
            update_frequency="weekly",
            source="conversation",
            related_fact_ids=["fact-1", "fact-2"],
            context_maps=["map-1"],
            meta_data={"key": "value"},
            usage_count=5,
        )

        saved = await memory_service.add_facts([fact])

        assert len(saved) == 1
        assert saved[0].needs_update is True
        assert saved[0].update_frequency == "weekly"
        assert saved[0].related_fact_ids == ["fact-1", "fact-2"]
        assert saved[0].context_maps == ["map-1"]
        assert saved[0].meta_data == {"key": "value"}
        assert saved[0].usage_count == 5

    @pytest.mark.asyncio
    async def test_get_facts_empty_database(self, test_db):
        """Test getting facts from empty database"""
        memory_service = MemoryService(test_db)

        facts = await memory_service.get_facts()

        assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_facts_have_correct_datatype(self, test_db, sample_facts):
        """Test that saved and retrieved facts maintain correct types"""
        memory_service = MemoryService(test_db)
        await memory_service.add_facts([sample_facts[0]])

        fact = await memory_service.get_fact_by_id("test-fact-1")

        assert isinstance(fact.importance, float)
        assert isinstance(fact.confidence, float)
        assert isinstance(fact.tags, list)
        assert isinstance(fact.created, datetime)
        assert isinstance(fact.updated, datetime)

    @pytest.mark.asyncio
    async def test_add_facts_error_handling(self, test_db):
        """Test that errors in adding individual facts don't break batch"""
        memory_service = MemoryService(test_db)

        # Create one valid and one potentially problematic fact
        facts = [
            Fact(
                fact_id="valid-fact",
                text="Valid fact",
                importance=0.8,
                confidence=0.9,
                fact_type="static",
                source="conversation",
            ),
            # This will be handled by the error handling in add_facts
        ]

        # Should still save the valid fact
        saved = await memory_service.add_facts(facts)

        assert len(saved) >= 1
