"""
Unit tests for MemoryAuditor - Duplicate detection and cleanup

Task 39: Deduplicate facts in memory
TDD approach with baby steps
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.memory_auditor import MemoryAuditor, DuplicateGroup, DeduplicationResult
from app.models.memory_v2 import Fact, FactModel


class TestMemoryAuditorDuplicateDetection:
    """Tests for duplicate fact detection"""

    def test_find_duplicates_exact_match(self):
        """Test: Find exact duplicate facts"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(
                fact_id="fact-1",
                text="User's name is Denis",
                importance=0.9,
                tags=["name"],
            ),
            Fact(
                fact_id="fact-2",
                text="User's name is Denis",
                importance=0.8,
                tags=["personal"],
            ),
        ]

        # Act
        duplicates = auditor.find_duplicates(facts)

        # Assert
        assert len(duplicates) == 1
        assert len(duplicates[0].facts) == 2
        assert duplicates[0].similarity_score >= 0.99

    def test_find_duplicates_similar_text(self):
        """Test: Find similar facts (>85% similarity)"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(
                fact_id="fact-1",
                text="User's name is Denis",
                importance=0.9,
                tags=["name"],
            ),
            Fact(
                fact_id="fact-2",
                text="The user's name is Denis",
                importance=0.7,
                tags=["personal"],
            ),
        ]

        # Act
        duplicates = auditor.find_duplicates(facts)

        # Assert
        assert len(duplicates) == 1
        assert duplicates[0].similarity_score >= 0.80

    def test_find_duplicates_no_duplicates(self):
        """Test: No duplicates when facts are different"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(
                fact_id="fact-1",
                text="User's name is Denis",
                importance=0.9,
                tags=["name"],
            ),
            Fact(
                fact_id="fact-2",
                text="User lives in Tel Aviv",
                importance=0.8,
                tags=["location"],
            ),
        ]

        # Act
        duplicates = auditor.find_duplicates(facts)

        # Assert
        assert len(duplicates) == 0

    def test_find_duplicates_empty_list(self):
        """Test: Empty list returns no duplicates"""
        # Arrange
        auditor = MemoryAuditor()

        # Act
        duplicates = auditor.find_duplicates([])

        # Assert
        assert len(duplicates) == 0

    def test_find_duplicates_single_fact(self):
        """Test: Single fact returns no duplicates"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(
                fact_id="fact-1",
                text="User's name is Denis",
                importance=0.9,
                tags=["name"],
            ),
        ]

        # Act
        duplicates = auditor.find_duplicates(facts)

        # Assert
        assert len(duplicates) == 0


class TestMemoryAuditorMerge:
    """Tests for merging duplicate facts"""

    def test_select_primary_fact_highest_importance(self):
        """Test: Select fact with highest importance as primary"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(fact_id="fact-1", text="User's name is Denis", importance=0.7),
            Fact(fact_id="fact-2", text="User's name is Denis", importance=0.9),
            Fact(fact_id="fact-3", text="User's name is Denis", importance=0.5),
        ]

        # Act
        primary = auditor.select_primary_fact(facts)

        # Assert
        assert primary.fact_id == "fact-2"
        assert primary.importance == 0.9

    def test_merge_tags_from_duplicates(self):
        """Test: Merge tags from all duplicates"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(
                fact_id="fact-1",
                text="User's name is Denis",
                importance=0.9,
                tags=["name", "personal"],
            ),
            Fact(
                fact_id="fact-2",
                text="User's name is Denis",
                importance=0.7,
                tags=["identity", "user"],
            ),
        ]

        # Act
        merged_tags = auditor.merge_tags(facts)

        # Assert
        assert set(merged_tags) == {"name", "personal", "identity", "user"}

    def test_sum_usage_counts(self):
        """Test: Sum usage counts from all duplicates"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(fact_id="fact-1", text="User's name is Denis", usage_count=5),
            Fact(fact_id="fact-2", text="User's name is Denis", usage_count=3),
            Fact(fact_id="fact-3", text="User's name is Denis", usage_count=2),
        ]

        # Act
        total_usage = auditor.sum_usage_counts(facts)

        # Assert
        assert total_usage == 10


class TestMemoryAuditorDeduplicate:
    """Tests for full deduplication process"""

    def test_create_merged_fact(self):
        """Test: Create merged fact from duplicates"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(
                fact_id="fact-1",
                text="User's name is Denis",
                importance=0.9,
                tags=["name"],
                usage_count=5,
            ),
            Fact(
                fact_id="fact-2",
                text="User's name is Denis",
                importance=0.7,
                tags=["personal"],
                usage_count=3,
            ),
        ]

        # Act
        merged = auditor.create_merged_fact(facts)

        # Assert
        assert merged.fact_id == "fact-1"  # Highest importance
        assert merged.importance == 0.9
        assert set(merged.tags) == {"name", "personal"}
        assert merged.usage_count == 8

    def test_get_facts_to_delete(self):
        """Test: Get list of fact IDs to delete after merge"""
        # Arrange
        auditor = MemoryAuditor()
        facts = [
            Fact(fact_id="fact-1", text="User's name is Denis", importance=0.9),
            Fact(fact_id="fact-2", text="User's name is Denis", importance=0.7),
            Fact(fact_id="fact-3", text="User's name is Denis", importance=0.5),
        ]
        primary_id = "fact-1"

        # Act
        to_delete = auditor.get_facts_to_delete(facts, primary_id)

        # Assert
        assert set(to_delete) == {"fact-2", "fact-3"}
        assert "fact-1" not in to_delete


class TestMemoryAuditorAsync:
    """Tests for async database deduplication"""

    @pytest.mark.asyncio
    async def test_deduplicate_all_dry_run(self):
        """Test: Dry run reports duplicates without deleting"""
        # Arrange
        auditor = MemoryAuditor()

        # Mock MemoryService
        mock_memory_service = AsyncMock()

        # Create mock FactModel objects with to_dataclass method
        mock_fact_1 = MagicMock()
        mock_fact_1.to_dataclass.return_value = Fact(
            fact_id="fact-1",
            text="User's name is Denis",
            importance=0.9,
        )
        mock_fact_2 = MagicMock()
        mock_fact_2.to_dataclass.return_value = Fact(
            fact_id="fact-2",
            text="User's name is Denis",
            importance=0.7,
        )

        mock_memory_service.get_facts.return_value = [mock_fact_1, mock_fact_2]

        # Act
        result = await auditor.deduplicate_all(mock_memory_service, dry_run=True)

        # Assert
        assert result.groups_found == 1
        assert result.facts_deleted == 1  # Would delete 1 duplicate
        assert result.facts_merged == 0  # Dry run, no actual merge
        mock_memory_service.delete_fact.assert_not_called()

    @pytest.mark.asyncio
    async def test_deduplicate_all_actual_merge(self):
        """Test: Actually merge and delete duplicates"""
        # Arrange
        auditor = MemoryAuditor()

        mock_memory_service = AsyncMock()

        mock_fact_1 = MagicMock()
        mock_fact_1.to_dataclass.return_value = Fact(
            fact_id="fact-1",
            text="User's name is Denis",
            importance=0.9,
            tags=["name"],
            usage_count=5,
        )
        mock_fact_2 = MagicMock()
        mock_fact_2.to_dataclass.return_value = Fact(
            fact_id="fact-2",
            text="User's name is Denis",
            importance=0.7,
            tags=["personal"],
            usage_count=3,
        )

        mock_memory_service.get_facts.return_value = [mock_fact_1, mock_fact_2]

        # Act
        result = await auditor.deduplicate_all(mock_memory_service, dry_run=False)

        # Assert
        assert result.groups_found == 1
        assert result.facts_merged == 1
        assert result.facts_deleted == 1

        # Verify update was called for primary fact
        mock_memory_service.update_fact.assert_called_once()
        call_kwargs = mock_memory_service.update_fact.call_args[1]
        assert call_kwargs["fact_id"] == "fact-1"
        assert set(call_kwargs["tags"]) == {"name", "personal"}
        assert call_kwargs["usage_count"] == 8

        # Verify delete was called for duplicate
        mock_memory_service.delete_fact.assert_called_once_with("fact-2")

    @pytest.mark.asyncio
    async def test_deduplicate_all_no_duplicates(self):
        """Test: No action when no duplicates found"""
        # Arrange
        auditor = MemoryAuditor()

        mock_memory_service = AsyncMock()

        mock_fact_1 = MagicMock()
        mock_fact_1.to_dataclass.return_value = Fact(
            fact_id="fact-1",
            text="User's name is Denis",
            importance=0.9,
        )
        mock_fact_2 = MagicMock()
        mock_fact_2.to_dataclass.return_value = Fact(
            fact_id="fact-2",
            text="User lives in Tel Aviv",
            importance=0.8,
        )

        mock_memory_service.get_facts.return_value = [mock_fact_1, mock_fact_2]

        # Act
        result = await auditor.deduplicate_all(mock_memory_service, dry_run=False)

        # Assert
        assert result.groups_found == 0
        assert result.facts_merged == 0
        assert result.facts_deleted == 0
        mock_memory_service.update_fact.assert_not_called()
        mock_memory_service.delete_fact.assert_not_called()

    @pytest.mark.asyncio
    async def test_deduplicate_all_handles_errors(self):
        """Test: Handles errors gracefully and continues"""
        # Arrange
        auditor = MemoryAuditor()

        mock_memory_service = AsyncMock()
        mock_memory_service.get_facts.side_effect = Exception("Database error")

        # Act
        result = await auditor.deduplicate_all(mock_memory_service, dry_run=False)

        # Assert
        assert len(result.errors) == 1
        assert "Database error" in result.errors[0]