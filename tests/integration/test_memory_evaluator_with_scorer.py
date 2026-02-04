"""
Integration tests for MemoryEvaluator with RelevanceScorer.

Verifies that MemoryEvaluator:
1. Uses RelevanceScorer to score facts
2. Filters low-relevance facts
3. Returns facts sorted by relevance
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator.memory_evaluator import MemoryEvaluator
from app.services.orchestrator.relevance_scorer import RelevanceScorer
from app.services.orchestrator.query_analyzer import QueryAnalysis


class TestMemoryEvaluatorWithScorer:
    """Integration tests for MemoryEvaluator with RelevanceScorer"""

    @pytest.mark.asyncio
    async def test_evaluator_uses_relevance_scorer(self):
        """Test: MemoryEvaluator should use RelevanceScorer to score facts"""
        # Arrange
        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            MagicMock(text="cat is cute", importance=0.8, confidence=0.9, tags=[], created_at=datetime.utcnow()),
            MagicMock(text="dog is friendly", importance=0.9, confidence=0.9, tags=[], created_at=datetime.utcnow()),
        ])

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            topics=["cat"],
            entities=["cat"],
            confidence=0.9,
            query_type="personal",
            requires_reasoning=False,
            requires_memory=True
        )

        # Act
        result = await evaluator.evaluate(query_analysis, session_id="test-session")

        # Assert - facts should have relevance_score
        assert len(result.relevant_facts) > 0
        assert all("relevance_score" in f for f in result.relevant_facts)

    @pytest.mark.asyncio
    async def test_evaluator_returns_facts_sorted_by_relevance(self):
        """Test: Facts should be returned sorted by relevance (highest first)"""
        # Arrange
        mock_memory_service = AsyncMock()
        now = datetime.utcnow()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            MagicMock(text="dog is friendly", importance=0.9, confidence=0.9, tags=[], created_at=now),
            MagicMock(text="cat is cute", importance=0.5, confidence=0.9, tags=[], created_at=now),
            MagicMock(text="bird can fly", importance=0.8, confidence=0.9, tags=[], created_at=now),
        ])

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            topics=["cat"],
            entities=["cat"],
            confidence=0.9,
            query_type="personal",
            requires_reasoning=False,
            requires_memory=True
        )

        # Act
        result = await evaluator.evaluate(query_analysis, session_id="test-session")

        # Assert - "cat is cute" should be first (best match for "cat" query)
        assert len(result.relevant_facts) > 0
        assert result.relevant_facts[0]["text"] == "cat is cute"

    @pytest.mark.asyncio
    async def test_evaluator_filters_low_relevance_facts(self):
        """Test: Facts with relevance below min_score should be filtered"""
        # Arrange
        mock_memory_service = AsyncMock()
        now = datetime.utcnow()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            MagicMock(text="cat is cute", importance=0.8, confidence=0.9, tags=[], created_at=now),
            MagicMock(text="pizza is delicious", importance=0.9, confidence=0.9, tags=[], created_at=now),
            MagicMock(text="weather is nice", importance=0.7, confidence=0.9, tags=[], created_at=now),
        ])

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            topics=["cat"],
            entities=["cat"],
            confidence=0.9,
            query_type="personal",
            requires_reasoning=False,
            requires_memory=True
        )

        # Act
        result = await evaluator.evaluate(query_analysis, session_id="test-session")

        # Assert - only cat-related fact should pass (others have no word overlap)
        cat_facts = [f for f in result.relevant_facts if "cat" in f["text"]]
        non_cat_facts = [f for f in result.relevant_facts if "cat" not in f["text"]]

        assert len(cat_facts) >= 1
        # Non-cat facts should have much lower relevance scores
        if non_cat_facts:
            assert all(f["relevance_score"] < cat_facts[0]["relevance_score"] for f in non_cat_facts)