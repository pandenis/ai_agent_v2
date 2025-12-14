"""Tests for DecisionEngine component"""
import pytest
from app.services.orchestrator.decision_engine import DecisionEngine, Decision
from app.services.orchestrator.query_analyzer import QueryAnalysis
from app.services.orchestrator.memory_evaluator import MemoryEvaluation


class TestDecisionEngine:
    """Test suite for DecisionEngine"""

    def test_decide_returns_decision(self):
        """Test: decide() should return Decision object"""
        # Arrange
        engine = DecisionEngine()
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
        memory_eval = MemoryEvaluation(
            coverage_score=0.9,
            relevant_facts=[{"text": "User is Denis"}],
            gaps=[],
            confidence=0.9
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert isinstance(result, Decision)
        assert result.strategy in ["direct", "enhanced", "deep_reasoning"]
        assert result.estimated_time > 0
        assert result.estimated_cost >= 0