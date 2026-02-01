"""
Tests for RelevanceScorer - relevance-based fact scoring.

Tests the scoring formula:
    relevance = 0.5 * text_similarity + 0.2 * recency + 0.3 * importance

TDD Baby Steps:
1. text_similarity_identical → 1.0 ✅
2. text_similarity_no_overlap → 0.0 ✅
3. text_similarity_partial → 0.0-1.0 ✅
4. text_similarity_case_insensitive
5. text_similarity_empty → 0.0
6. recency_score_today → 1.0
7. recency_score_90_days_old → 0.0
8. recency_score_45_days_old → ~0.5
9. calculate_relevance combines all
10. score_facts returns sorted
"""

import pytest
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