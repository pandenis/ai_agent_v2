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

    @pytest.mark.asyncio
    async def test_identify_gaps_when_no_facts(self):
        """Test: Should identify all topics as gaps when no facts"""
        # Arrange
        query_analysis = QueryAnalysis(
            complexity="medium",
            intent="question",
            query_type="factual",
            entities=["React", "TypeScript"],
            topics=["programming", "frontend"],
            requires_memory=True,
            requires_reasoning=False,
            confidence=0.8
        )

        # Mock empty facts
        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.return_value = []

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert
        assert result.coverage_score == 0.0
        assert "programming" in result.gaps
        assert "frontend" in result.gaps

    @pytest.mark.asyncio
    async def test_no_gaps_when_facts_cover_topics(self):
        """Test: No gaps when facts exist for all topics"""
        # Arrange
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

        # Mock facts that cover programming topic
        mock_facts = [
            {"text": "User knows Python programming", "importance": 4.5},
            {"text": "User is learning programming", "importance": 4.0}
        ]

        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.return_value = mock_facts

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert
        assert result.coverage_score > 0.5
        assert "programming" not in result.gaps  # Should not have gap

    @pytest.mark.asyncio
    async def test_low_coverage_with_one_fact(self):
        """Test: Low coverage (0.5) when only one fact found"""
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

        # Mock with only 1 fact (low importance)
        mock_facts = [{"text": "User's name is Denis", "importance": 0.3, "confidence": 0.3}]

        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.return_value = mock_facts

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert
        assert 0.5 <= result.coverage_score <= 0.65
        assert len(result.relevant_facts) == 1

    @pytest.mark.asyncio
    async def test_high_coverage_with_many_facts(self):
        """Test: High coverage (0.9) when 5+ facts found"""
        # Arrange
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

        # Mock with 5 facts
        mock_facts = [
            {"text": f"Python fact {i}", "importance": 0.5, "confidence": 0.5}
            for i in range(5)
        ]

        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.return_value = mock_facts

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert
        assert result.coverage_score >= 0.9
        assert len(result.relevant_facts) == 5

    @pytest.mark.asyncio
    async def test_handles_memory_service_error_gracefully(self):
        """Test: Should handle memory service errors gracefully"""
        # Arrange
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

        # Mock memory service that raises exception
        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.side_effect = Exception("Database error")

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert
        assert result.coverage_score == 0.0  # Should return 0 coverage on error
        assert len(result.relevant_facts) == 0
        assert len(result.gaps) > 0  # Should identify all topics as gaps

    @pytest.mark.asyncio
    async def test_coverage_considers_importance(self):
        """Test: Coverage should consider fact importance, not just count"""
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

        # High importance fact - should give good coverage
        high_importance_facts = [
            {"text": "User's name is Denis", "importance": 0.95, "confidence": 0.98}
        ]

        mock_memory_service = AsyncMock()
        mock_memory_service.search_facts.return_value = high_importance_facts

        evaluator = MemoryEvaluator(memory_service=mock_memory_service)

        # Act
        result = await evaluator.evaluate(query_analysis, "test-session")

        # Assert - 1 high-importance fact should give coverage >= 0.7
        assert result.coverage_score >= 0.7, \
            f"1 high-importance fact should give coverage >= 0.7, got {result.coverage_score}"