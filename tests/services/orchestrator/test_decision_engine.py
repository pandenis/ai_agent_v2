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

    def test_deep_reasoning_when_low_coverage(self):
        """Test: Deep reasoning when coverage is too low (<0.7)"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="simple",  # Even simple query
            intent="question",
            query_type="factual",
            entities=["unknown"],
            topics=["general"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.3,  # Too low!
            relevant_facts=[],
            gaps=["unknown topic"],
            confidence=0.5
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "deep_reasoning"  # Falls back to deep
        assert result.agent == "mixtral"

    def test_default_agent_for_unknown_topic(self):
        """Test: Uses llama3 as default for unknown topics"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="question",
            query_type="factual",
            entities=["something"],
            topics=["unknown_topic"],  # Not in AGENT_MAP
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.8,
            relevant_facts=[{"text": "Some fact"}],
            gaps=[],
            confidence=0.8
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "enhanced"
        assert result.agent == "llama3"  # Default fallback

    def test_enhanced_at_coverage_boundary_0_7(self):
        """Test: Enhanced strategy at exactly 0.7 coverage"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="question",
            query_type="factual",
            entities=["test"],
            topics=["general"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.7,  # Exactly at boundary
            relevant_facts=[{"text": "fact"}],
            gaps=[],
            confidence=0.8
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "enhanced"
        assert result.agent == "llama3"

    def test_direct_at_coverage_boundary_0_9(self):
        """Test: Direct strategy at exactly 0.9 coverage"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="simple",
            intent="question",
            query_type="factual",
            entities=["test"],
            topics=["general"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.9
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.9,  # Exactly at boundary
            relevant_facts=[{"text": "fact"}],
            gaps=[],
            confidence=0.9
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "direct"
        assert result.agent is None
        assert result.estimated_cost == 0.0

    def test_empty_topics_uses_default_agent(self):
        """Test: Empty topics list uses llama3 default"""
        # Arrange
        engine = DecisionEngine()
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="question",
            query_type="factual",
            entities=[],
            topics=[],  # Empty!
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )
        memory_eval = MemoryEvaluation(
            coverage_score=0.8,
            relevant_facts=[],
            gaps=[],
            confidence=0.8
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert
        assert result.strategy == "enhanced"
        assert result.agent == "llama3"

    def test_all_decisions_use_memory(self):
        """Test: All strategies should use memory"""
        # Arrange
        engine = DecisionEngine()

        # Test all three strategies
        strategies = [
            # Direct
            (QueryAnalysis("simple", "question", "factual", [], ["general"], True, False, 0.9),
             MemoryEvaluation(0.95, [], [], 0.9)),
            # Enhanced
            (QueryAnalysis("medium", "question", "factual", [], ["programming"], True, False, 0.8),
             MemoryEvaluation(0.75, [], [], 0.8)),
            # Deep
            (QueryAnalysis("complex", "question", "reasoning", [], ["analysis"], True, True, 0.7),
             MemoryEvaluation(0.3, [], [], 0.6))
        ]

        for query_analysis, memory_eval in strategies:
            # Act
            result = engine.decide(query_analysis, memory_eval)

            # Assert
            assert result.use_memory is True

    def test_low_confidence_triggers_enhanced_despite_high_coverage(self):
        """Test: Low memory confidence should trigger enhanced even with high coverage"""
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
        # High coverage BUT low confidence - can't trust memory!
        memory_eval = MemoryEvaluation(
            coverage_score=0.95,
            relevant_facts=[{"text": "Maybe user is Denis"}],
            gaps=[],
            confidence=0.4  # LOW confidence!
        )

        # Act
        result = engine.decide(query_analysis, memory_eval)

        # Assert - should NOT use direct because confidence is too low
        assert result.strategy == "enhanced", \
            f"Low confidence ({memory_eval.confidence}) should trigger enhanced, got {result.strategy}"