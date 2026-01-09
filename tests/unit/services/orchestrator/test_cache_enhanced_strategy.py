"""
Task 35: Test enhanced strategy caching
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


class TestEnhancedStrategyCaching:
    """Tests for enhanced strategy caching."""

    @pytest.mark.asyncio
    async def test_enhanced_strategy_response_is_cached(self):
        """
        Test: Enhanced strategy responses should be cached for reuse.

        CURRENT: Second call = full processing (~3s)
        EXPECTED: Second call = from cache (~10ms)
        """
        # Arrange
        mock_memory_service = Mock()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            {"text": "User prefers Python", "importance": 0.75, "confidence": 0.8}
        ])
        mock_memory_service.add_facts = AsyncMock()

        mock_agent = Mock()
        mock_agent.generate = AsyncMock(return_value={
            "response": "Enhanced AI response",
            "status": "success"
        })

        mock_agent_factory = Mock()
        mock_agent_factory.create_agent = Mock(return_value=mock_agent)

        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory
        )

        # Mock medium coverage (triggers enhanced)
        mock_eval = Mock()
        mock_eval.coverage_score = 0.75
        mock_eval.confidence = 0.8
        mock_eval.relevant_facts = [{"text": "User prefers Python", "importance": 0.75}]
        mock_eval.gaps = ["some minor gaps"]
        mock_eval.has_sufficient_coverage = False

        with patch.object(orchestrator.memory_evaluator, 'evaluate', new_callable=AsyncMock) as mock_evaluate:
            mock_evaluate.return_value = mock_eval

            # Act - First call
            result1 = await orchestrator.process_query(
                query="What programming language should I learn?",
                session_id="test-enhanced-cache"
            )

            # Act - Second call (should be cached)
            result2 = await orchestrator.process_query(
                query="What programming language should I learn?",
                session_id="test-enhanced-cache"
            )

        # Assert
        assert result1["metadata"]["strategy"] == "enhanced"
        assert result2["metadata"].get("cached") == True  # ← KEY ASSERTION
        assert mock_agent.generate.call_count == 1  # AI called only once