"""
Task 37: Tests for memory_coverage in response metadata.

Problem: memory_coverage always returns null in response
Expected: memory_coverage: 0.0-1.0 (actual score from MemoryEvaluator)
"""
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.orchestrator.orchestrator import IntelligentOrchestrator
from app.services.orchestrator.memory_evaluator import MemoryEvaluation


# ==========================================
# Fixtures (copied from test_orchestrator.py)
# ==========================================

@pytest.fixture
def mock_memory_service():
    """Create a mock memory service"""
    service = Mock()
    service.search_facts = AsyncMock(return_value=[])
    service.get_important_facts = AsyncMock(return_value=[])
    service.save_interaction = AsyncMock()
    service.add_fact = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_agent():
    """Create a mock AI agent"""
    agent = AsyncMock()
    agent.name = "test-agent"
    agent.generate = AsyncMock(return_value={"response": "This is a test AI response", "status": "success"})
    return agent


@pytest.fixture
def mock_agent_factory(mock_agent):
    """Create a mock agent factory"""
    factory = Mock()
    factory.create_agent = Mock(return_value=mock_agent)
    return factory


@pytest.fixture
def mock_fact_extractor():
    """Create a mock fact extractor"""
    extractor = AsyncMock()
    extractor.extract_facts = AsyncMock(return_value=[])
    return extractor


@pytest.fixture
def orchestrator(mock_memory_service, mock_agent_factory, mock_fact_extractor):
    """Create an orchestrator instance for testing"""
    return IntelligentOrchestrator(
        memory_service=mock_memory_service,
        agent_factory=mock_agent_factory,
        fact_extractor=mock_fact_extractor
    )


# ==========================================
# Tests
# ==========================================

class TestMemoryCoverageInResponse:
    """Tests for memory_coverage appearing correctly in API responses."""

    @pytest.mark.asyncio
    async def test_response_includes_memory_coverage(self, orchestrator):
        """Test: Response metadata should include memory_coverage field."""
        # Arrange - Mock memory evaluator with specific coverage score
        mock_eval = MemoryEvaluation(
            coverage_score=0.85,
            relevant_facts=[{"text": "User's name is Denis", "importance": 0.9}],
            gaps=[],
            confidence=0.85
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        # Act
        result = await orchestrator.process_query(
            query="What is my name?",
            session_id="test-session"
        )

        # Assert - memory_coverage should be present
        assert "metadata" in result
        assert "memory_coverage" in result["metadata"], "metadata should contain 'memory_coverage' field"

    @pytest.mark.asyncio
    async def test_memory_coverage_value_matches_evaluator(self, orchestrator):
        """Test: memory_coverage should match the evaluator's coverage_score."""
        # Arrange
        mock_eval = MemoryEvaluation(
            coverage_score=0.72,
            relevant_facts=[{"text": "Some fact", "importance": 0.7}],
            gaps=["partial"],
            confidence=0.7
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        # Act
        result = await orchestrator.process_query(
            query="Tell me something",
            session_id="test-session"
        )

        # Assert - memory_coverage should be 0.72 (rounded)
        assert result["metadata"]["memory_coverage"] == 0.72

    @pytest.mark.asyncio  
    async def test_memory_coverage_is_float_between_0_and_1(self, orchestrator):
        """Test: memory_coverage should be a float between 0.0 and 1.0."""
        # Arrange
        mock_eval = MemoryEvaluation(
            coverage_score=0.25,
            relevant_facts=[],
            gaps=["missing information"],
            confidence=0.3
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        # Act
        result = await orchestrator.process_query(
            query="Tell me about quantum physics",
            session_id="test-session"
        )

        # Assert
        assert "memory_coverage" in result["metadata"], "metadata should contain memory_coverage"
        memory_coverage = result["metadata"]["memory_coverage"]
        assert isinstance(memory_coverage, float), "memory_coverage should be a float"
        assert 0.0 <= memory_coverage <= 1.0, "memory_coverage should be between 0 and 1"
