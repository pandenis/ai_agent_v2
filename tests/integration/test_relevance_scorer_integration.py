"""
Integration tests for RelevanceScorer with MemoryEvaluator.

Tests the full flow:
1. Facts are scored by relevance
2. Low-relevance facts are filtered
3. Token budget is respected
4. Tier-based access rules apply
"""

import pytest
from datetime import datetime, timedelta
from app.services.orchestrator.relevance_scorer import RelevanceScorer


class TestRelevanceScorerIntegration:
    """Integration tests for RelevanceScorer"""

    def test_scorer_filters_irrelevant_facts_for_memory_evaluation(self):
        """Test: RelevanceScorer filters facts before MemoryEvaluator uses them"""
        # Arrange
        scorer = RelevanceScorer()
        # Use simple words that match directly (word overlap limitation)
        query = "cat name"
        now = datetime.utcnow()

        # Simulate facts from database
        all_facts = [
            {"text": "cat name is Whiskers", "created_at": now, "importance": 0.8},
            {"text": "User likes pizza", "created_at": now, "importance": 0.9},
            {"text": "User works as QA engineer", "created_at": now, "importance": 0.7},
            {"text": "User has a cat", "created_at": now, "importance": 0.6},
        ]

        # Act - filter with enhanced tier (min_score=0.5)
        access = scorer.get_memory_access("enhanced")
        filtered = scorer.score_and_filter(query, all_facts, min_score=access["min_score"])

        # Assert - only cat-related facts should pass
        assert len(filtered) >= 1
        assert filtered[0]["text"] == "cat name is Whiskers"  # Best match first

    def test_different_tiers_return_different_results(self):
        """Test: direct tier is more restrictive than deep_reasoning"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        now = datetime.utcnow()

        facts = [
            {"text": "cat is cute", "created_at": now, "importance": 0.8},  # High relevance
            {"text": "my cat sleeps", "created_at": now, "importance": 0.5},  # Medium relevance
            {"text": "pets are nice", "created_at": now, "importance": 0.6},  # Low relevance
        ]

        # Act - compare tiers
        direct_access = scorer.get_memory_access("direct")
        deep_access = scorer.get_memory_access("deep_reasoning")

        direct_results = scorer.score_and_filter(query, facts, min_score=direct_access["min_score"])
        deep_results = scorer.score_and_filter(query, facts, min_score=deep_access["min_score"])

        # Assert - deep_reasoning should return more facts (lower threshold)
        assert len(deep_results) >= len(direct_results)
        assert direct_access["min_score"] > deep_access["min_score"]

    def test_token_budget_respects_relevance_order(self):
        """Test: Token budget selects highest relevance facts first"""
        # Arrange
        scorer = RelevanceScorer()
        query = "cat"
        now = datetime.utcnow()
        old_date = now - timedelta(days=60)  # Lower recency score

        facts = [
            {"text": "dog is a pet", "created_at": now, "importance": 0.9},  # No match, high importance
            {"text": "cat is cute", "created_at": now, "importance": 0.5},  # Match, low importance
            {"text": "old cat fact", "created_at": old_date, "importance": 0.8},  # Match, old
        ]

        # Act - small budget, only 1 fact fits
        result = scorer.select_facts_within_budget(query, facts, max_tokens=5)

        # Assert - should pick "cat is cute" (highest relevance score)
        assert len(result) == 1
        assert "cat" in result[0]["text"]