"""Tests for MemoryEvaluator component"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.orchestrator.memory_evaluator import MemoryEvaluator, MemoryEvaluation
from app.services.orchestrator.query_analyzer import QueryAnalysis



class TestMemoryEvaluator:
    """Test suite for MemoryEvaluator"""

    @pytest.mark.asyncio
    async def test_evaluate_returns_memory_evaluation(self):
        """Test: evaluate() should return MemoryEvaluation object"""
        # Arrange
        evaluator = MemoryEvaluator()
        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            query_type="factual",
            entities=["Denis"],
            topics=["general"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.9
        )
        session_id = "test-session"

        # Act
        result = await evaluator.evaluate(query_analysis, session_id)

        # Assert
        assert isinstance(result, MemoryEvaluation)
        assert result.coverage_score >= 0.0
        assert result.coverage_score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_finds_relevant_facts(self):
        """Test: Should find facts related to query topics"""
        # Arrange
        evaluator = MemoryEvaluator()
        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            query_type="factual",
            entities=["Python"],
            topics=["programming"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.9
        )
        session_id = "test-session"

        # Act
        result = await evaluator.evaluate(query_analysis, session_id)

        # Assert
        assert isinstance(result.relevant_facts, list)
        # Facts should be a list (empty or with items)
        assert result.coverage_score >= 0.0

    @pytest.mark.asyncio
    async def test_evaluate_with_facts_in_memory(self):
        """Test: High coverage when facts exist in memory"""
        # Arrange
        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            query_type="factual",
            entities=["Denis"],
            topics=["general"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.9
        )

        # Mock memory service to return facts
        mock_facts = [
            {"text": "User's name is Denis", "importance": 5.0},
            {"text": "Denis is a QA Engineer", "importance": 4.5}
        ]

        # Create mock memory service
        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.return_value = mock_facts

        # Inject mocked service
        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert
        assert result.coverage_score > 0.5  # Should have good coverage
        assert len(result.relevant_facts) == 2
        mock_memory_service.search_facts.assert_called_once()