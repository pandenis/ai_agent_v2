"""
Unit tests for MemoryAuditor - Duplicate detection and cleanup

Task 39: Deduplicate facts in memory
TDD approach with baby steps
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.memory_auditor import MemoryAuditor, DuplicateGroup
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
        assert duplicates[0].similarity_score >= 0.85

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