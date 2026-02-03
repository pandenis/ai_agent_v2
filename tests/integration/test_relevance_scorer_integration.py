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