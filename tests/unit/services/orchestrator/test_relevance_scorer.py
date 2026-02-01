"""
Tests for RelevanceScorer - relevance-based fact scoring.

Tests the scoring formula:
    relevance = 0.5 * text_similarity + 0.2 * recency + 0.3 * importance

TDD Baby Steps:
1. text_similarity_identical → 1.0 ✅
2. text_similarity_no_overlap → 0.0 ✅
3. text_similarity_partial → 0.0-1.0 ✅
4. text_similarity_case_insensitive ✅
5. text_similarity_empty → 0.0 ✅
6. recency_score_today → 1.0 ✅
7. recency_score_90_days_old → 0.0 ✅
8. recency_score_45_days_old → ~0.5 ✅
9. calculate_relevance combines all ✅
10. score_facts returns sorted ✅

Task 4.2 - min_score threshold:
11. score_and_filter removes low scores ✅
12. score_and_filter keeps high scores ✅
13. score_and_filter with zero threshold returns all ✅

Task 4.3 - tier-based access:
14. get_memory_access for direct strategy
15. get_memory_access for enhanced strategy
16. get_memory_access for deep_reasoning strategy
17. direct has highest min_score, deep_reasoning lowest
"""

import pytest
from datetime import datetime, timedelta
from app.services.orchestrator.relevance_scorer import RelevanceScorer


class TestTextSimilarity:
    """Tests for text similarity calculation"""

    def test_text_similarity_identical_words_returns_one(self):
        """Test: Identical single words should return 1.0"""
        # Arrange
        scorer = RelevanceScorer()

        # Act
        result = scorer.text_similarity("cat", "cat")

        # Assert
        assert result == 1.0

    def test_text_similarity_no_overlap_returns_zero(self):
        """Test: Completely different words should return 0.0"""
        # Arrange
        scorer = RelevanceScorer()

        # Act
        result = scorer.text_similarity("cat", "dog")

        # Assert
        assert result == 0.0

    def test_text_similarity_partial_overlap_returns_ratio(self):
        """Test: Partial word overlap returns Jaccard ratio"""
        # Arrange
        scorer = RelevanceScorer()

        # Act - "cats" is shared, 4 unique words total
        # query: {i, love, cats} = 3 words
        # text: {cats, are, great} = 3 words
        # intersection: {cats} = 1 word
        # union: {i, love, cats, are, great} = 5 words
        # Jaccard = 1/5 = 0.2
        result = scorer.text_similarity("I love cats", "cats are great")

        # Assert
        assert result == 0.2

    def test_text_similarity_case_insensitive(self):
        """Test: Comparison should be case-insensitive"""
        # Arrange
        scorer = RelevanceScorer()

        # Act
        result = scorer.text_similarity("CAT", "cat")

        # Assert
        assert result == 1.0

    def test_text_similarity_empty_query_returns_zero(self):
        """Test: Empty query should return 0.0 (no division by zero)"""
        # Arrange
        scorer = RelevanceScorer()

        # Act
        result = scorer.text_similarity("", "cat")

        # Assert
        assert result == 0.0


class TestRecencyScore:
    """Tests for recency score calculation"""

    def test_recency_score_today_returns_one(self):
        """Test: Fact created today should return 1.0"""
        # Arrange
        scorer = RelevanceScorer()
        now = datetime.utcnow()

        # Act
        result = scorer.recency_score(now)

        # Assert
        assert result == 1.0

    def test_recency_score_90_days_old_returns_zero(self):
        """Test: Fact created 90+ days ago should return 0.0"""
        # Arrange
        scorer = RelevanceScorer()
        old_date = datetime.utcnow() - timedelta(days=90)

        # Act
        result = scorer.recency_score(old_date)

        # Assert
        assert result == 0.0

    def test_recency_score_45_days_old_returns_half(self):
        """Test: Fact created 45 days ago should return ~0.5"""
        # Arrange
        scorer = RelevanceScorer()
        mid_date = datetime.utcnow() - timedelta(days=45)

        # Act
        result = scorer.recency_score(mid_date)

        # Assert - 45/90 = 0.5, so score = 1.0 - 0.5 = 0.5
        assert result == 0.5


class TestCalculateRelevance:
    """Tests for combined relevance scoring"""

    def test_calculate_relevance_combines_all_components(self):
        """Test: Relevance = 0.5*similarity + 0.2*recency + 0.3*importance"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        fact_text = "cat"  # similarity = 1.0
        created_at = datetime.utcnow()  # recency = 1.0
        importance = 1.0

        # Act
        result = scorer.calculate_relevance(
            query=query,
            fact_text=fact_text,
            created_at=created_at,
            importance=importance
        )

        # Assert - 0.5*1.0 + 0.2*1.0 + 0.3*1.0 = 1.0
        assert result == 1.0


class TestScoreFacts:
    """Tests for batch fact scoring"""

    def test_score_facts_returns_sorted_by_relevance(self):
        """Test: Facts should be returned sorted by relevance (descending)"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        now = datetime.utcnow()

        facts = [
            {"text": "dog is friendly", "created_at": now, "importance": 0.9},  # Low similarity
            {"text": "cat is cute", "created_at": now, "importance": 0.5},  # High similarity
            {"text": "bird can fly", "created_at": now, "importance": 0.8},  # No similarity
        ]

        # Act
        result = scorer.score_facts(query, facts)

        # Assert - should be sorted by relevance descending
        assert len(result) == 3
        assert result[0]["text"] == "cat is cute"  # Best match
        assert result[0]["relevance_score"] > result[1]["relevance_score"]
        assert result[1]["relevance_score"] > result[2]["relevance_score"]


class TestScoreAndFilter:
    """Tests for min_score filtering"""

    def test_score_and_filter_removes_low_scores(self):
        """Test: Facts below min_score should be filtered out"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        now = datetime.utcnow()

        facts = [
            {"text": "cat is cute", "created_at": now, "importance": 0.8},  # High relevance
            {"text": "dog is friendly", "created_at": now, "importance": 0.5},  # Low relevance
            {"text": "bird can fly", "created_at": now, "importance": 0.5},  # No match
        ]

        # Act - filter with high threshold
        result = scorer.score_and_filter(query, facts, min_score=0.5)

        # Assert - only cat fact should pass
        assert len(result) == 1
        assert result[0]["text"] == "cat is cute"

    def test_score_and_filter_keeps_all_above_threshold(self):
        """Test: All facts above min_score should be kept and sorted"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        now = datetime.utcnow()

        facts = [
            {"text": "cat is cute", "created_at": now, "importance": 0.8},  # High
            {"text": "my cat sleeps", "created_at": now, "importance": 0.6},  # Medium
            {"text": "cat food", "created_at": now, "importance": 0.4},  # Lower but matches
        ]

        # Act - filter with low threshold
        result = scorer.score_and_filter(query, facts, min_score=0.3)

        # Assert - all should pass, sorted by relevance
        assert len(result) == 3
        assert result[0]["relevance_score"] >= result[1]["relevance_score"]
        assert result[1]["relevance_score"] >= result[2]["relevance_score"]

    def test_score_and_filter_zero_threshold_returns_all(self):
        """Test: min_score=0.0 should return all facts"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        now = datetime.utcnow()

        facts = [
            {"text": "cat is cute", "created_at": now, "importance": 0.8},
            {"text": "dog is friendly", "created_at": now, "importance": 0.5},
            {"text": "bird can fly", "created_at": now, "importance": 0.3},
        ]

        # Act - no filtering
        result = scorer.score_and_filter(query, facts, min_score=0.0)

        # Assert - all facts returned
        assert len(result) == 3


class TestMemoryAccessTiers:
    """Tests for tier-based memory access rules"""

    def test_get_memory_access_for_direct_strategy(self):
        """Test: Direct strategy should have high min_score threshold"""
        # Arrange
        scorer = RelevanceScorer()

        # Act
        access = scorer.get_memory_access("direct")

        # Assert
        assert access["min_score"] == 0.7
        assert access["fact_types"] == ["static"]

    def test_get_memory_access_for_enhanced_strategy(self):
        """Test: Enhanced strategy should have moderate min_score"""
        # Arrange
        scorer = RelevanceScorer()

        # Act
        access = scorer.get_memory_access("enhanced")

        # Assert
        assert access["min_score"] == 0.5
        assert "static" in access["fact_types"]
        assert "derived" in access["fact_types"]