"""Tests for MemoryEvaluator component"""
import pytest
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