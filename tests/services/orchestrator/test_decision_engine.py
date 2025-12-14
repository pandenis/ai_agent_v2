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

    def test_direct_strategy_when_high_coverage_simple(self):
        """Test: Direct strategy when coverage ≥ 0.9 and simple query"""
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
            coverage_score=0.95,  # High coverage
            relevant_facts=[{"text": "Fact 1"}, {"text": "Fact 2"}],
            gaps=[],
            confidence=0.9
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "direct"
        assert result.agent is None  # No AI needed!
        assert result.estimated_cost == 0.0  # Free!
        assert result.estimated_time < 0.2  # Fast!

    def test_enhanced_strategy_when_medium_coverage(self):
        """Test: Enhanced strategy when coverage ≥ 0.7 and medium complexity"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="question",
            query_type="factual",
            entities=["Python"],
            topics=["programming"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.75,  # Medium coverage
            relevant_facts=[{"text": "Denis knows Python"}],
            gaps=[],
            confidence=0.8
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "enhanced"
        assert result.agent == "deepseek"  # Programming topic → deepseek
        assert result.estimated_cost > 0  # Has cost
        assert result.estimated_time > 1  # Slower than direct

    def test_deep_reasoning_when_complex_query(self):
        """Test: Deep reasoning for complex queries"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="complex",
            intent="question",
            query_type="reasoning",
            entities=["quantum", "classical"],
            topics=["analysis"],
            requires_memory=True,
            requires_reasoning=True,
            confidence=0.7
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.3,  # Low coverage
            relevant_facts=[],
            gaps=["quantum computing", "classical computing"],
            confidence=0.6
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "deep_reasoning"
        assert result.agent == "mixtral"  # Powerful model
        assert result.estimated_cost > 0.001  # Higher cost
        assert result.estimated_time > 10  # Much slower

    def test_selects_medical_ai_for_medical_topic(self):
        """Test: Selects medical_ai for medical topics"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="question",
            query_type="factual",
            entities=["flu", "symptoms"],
            topics=["medical"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.7,
            relevant_facts=[],
            gaps=[],
            confidence=0.8
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "enhanced"
        assert result.agent == "medical_ai"

    def test_selects_mistral_for_creative_topic(self):
        """Test: Selects mistral for creative topics"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="command",
            query_type="creative",
            entities=["poem", "ocean"],
            topics=["creative"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.7,
            relevant_facts=[],
            gaps=[],
            confidence=0.8
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "enhanced"
        assert result.agent == "mistral"