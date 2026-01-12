"""
Task 38: Tests for cached flag in response metadata.

Problem: cached flag always null, even on cache hits
Expected: 
  - cached: false on first request (cache miss)
  - cached: true on second identical request (cache hit)
"""
import pytest
from unittest.mock import Mock, AsyncMock


class TestCachedFlagInResponse:
    """Tests for cached flag in orchestrator responses."""

    @pytest.mark.asyncio
    async def test_fresh_response_has_cached_false(self):
        """Test: Fresh (non-cached) response should have cached: false."""
        # Arrange
        from app.services.orchestrator.orchestrator import IntelligentOrchestrator
        
        mock_memory_service = Mock()
        mock_memory_service.search_facts = AsyncMock(return_value=[])
        mock_memory_service.get_important_facts = AsyncMock(return_value=[])
        mock_memory_service.save_interaction = AsyncMock()
        
        mock_agent_factory = Mock()
        mock_agent = Mock()
        mock_agent.process = AsyncMock(return_value="Test response")
        mock_agent_factory.get_agent = Mock(return_value=mock_agent)
        
        mock_fact_extractor = Mock()
        mock_fact_extractor.extract = AsyncMock(return_value=[])
        
        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory,
            fact_extractor=mock_fact_extractor
        )
        
        # Mock memory evaluator to return low coverage (triggers AI response)
        mock_eval = Mock()
        mock_eval.coverage_score = 0.3
        mock_eval.confidence = 0.4
        mock_eval.relevant_facts = []
        mock_eval.gaps = ["no information available"]
        mock_eval.has_sufficient_coverage = False
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        # Act - first request (fresh, not from cache)
        result = await orchestrator.process_query(
            query="What is the weather today?",
            session_id="test-session"
        )

        # Assert - fresh response should have cached: false
        assert "metadata" in result
        assert "cached" in result["metadata"], "metadata should contain 'cached' field"
        assert result["metadata"]["cached"] is False, "Fresh response should have cached: false"

    @pytest.mark.asyncio
    async def test_cached_response_has_cached_true(self):
        """Test: Cached response (second identical request) should have cached: true."""
        # Arrange
        from app.services.orchestrator.orchestrator import IntelligentOrchestrator
        from app.services.orchestrator.memory_evaluator import MemoryEvaluation
        
        mock_memory_service = Mock()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            {"text": "User's name is Denis", "importance": 0.9}
        ])
        mock_memory_service.get_important_facts = AsyncMock(return_value=[
            {"text": "User's name is Denis", "importance": 0.9}
        ])
        mock_memory_service.save_interaction = AsyncMock()
        
        mock_agent_factory = Mock()
        mock_fact_extractor = Mock()
        mock_fact_extractor.extract = AsyncMock(return_value=[])
        
        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory,
            fact_extractor=mock_fact_extractor
        )
        
        # Mock memory evaluator for high coverage (direct response - cacheable)
        mock_eval = MemoryEvaluation(
            coverage_score=0.95,
            relevant_facts=[{"text": "User's name is Denis", "importance": 0.9}],
            gaps=[],
            confidence=0.9
        )
        orchestrator.memory_evaluator.evaluate = AsyncMock(return_value=mock_eval)

        # Act - first request (should be cached: false)
        result1 = await orchestrator.process_query(
            query="What is my name?",
            session_id="test-session"
        )
        
        # Assert first request
        assert result1["metadata"]["cached"] is False, "First request should have cached: false"

        # Act - second identical request (should be cached: true)
        result2 = await orchestrator.process_query(
            query="What is my name?",
            session_id="test-session"
        )

        # Assert - second request should have cached: true
        assert result2["metadata"]["cached"] is True, "Second request should have cached: true"
