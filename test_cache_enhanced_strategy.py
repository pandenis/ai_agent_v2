"""
Task 35: Cache Performance Investigation

Test file for verifying enhanced strategy responses are cached.
Currently ONLY direct strategy is cached, causing 0.96x speedup issue.

Root Cause:
    if strategy.strategy == "direct":
        self.response_cache.set(query, result, context=user_context)
    # ^^^ Enhanced and deep_reasoning NEVER cached!

Expected Behavior:
    - direct: cached (TTL 1 hour)
    - enhanced: cached (TTL 30 min)  <-- NEW!
    - deep_reasoning: NOT cached (needs fresh data)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, '/home/claude/task35_cache_investigation')


class TestEnhancedStrategyCaching:
    """Tests for enhanced strategy caching - Task 35 fix."""

    @pytest.mark.asyncio
    async def test_enhanced_strategy_response_is_cached(self):
        """
        Test: Enhanced strategy responses should be cached for reuse.
        
        CURRENT BEHAVIOR (BUG):
            - First call: ~3s (AI processing)
            - Second call: ~3s (AI processing again - NOT cached!)
        
        EXPECTED BEHAVIOR (FIXED):
            - First call: ~3s (AI processing)
            - Second call: ~10ms (from cache)
        """
        # This test documents the expected behavior
        # It should FAIL with current implementation
        
        # Arrange
        from app.services.orchestrator.orchestrator import IntelligentOrchestrator
        from app.services.orchestrator.response_cache import ResponseCache
        
        mock_memory_service = Mock()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            {"text": "User prefers Python", "importance": 0.75, "confidence": 0.8}
        ])
        mock_memory_service.add_facts = AsyncMock()
        
        mock_agent = Mock()
        mock_agent.generate = AsyncMock(return_value={
            "response": "Enhanced AI response about Python",
            "status": "success"
        })
        
        mock_agent_factory = Mock()
        mock_agent_factory.create_agent = Mock(return_value=mock_agent)
        
        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory
        )
        
        # Mock memory evaluator to return medium coverage (triggers enhanced)
        mock_eval = Mock()
        mock_eval.coverage_score = 0.75  # Medium coverage = enhanced strategy
        mock_eval.confidence = 0.8
        mock_eval.relevant_facts = [{"text": "User prefers Python", "importance": 0.75}]
        mock_eval.gaps = ["some minor gaps"]
        mock_eval.has_sufficient_coverage = False  # Not enough for direct
        
        with patch.object(orchestrator.memory_evaluator, 'evaluate', new_callable=AsyncMock) as mock_evaluate:
            mock_evaluate.return_value = mock_eval
            
            # Act - First call (should process and cache)
            result1 = await orchestrator.process_query(
                query="What programming language should I learn?",
                session_id="test-enhanced-cache"
            )
            
            # Act - Second call (should return from cache)
            result2 = await orchestrator.process_query(
                query="What programming language should I learn?",
                session_id="test-enhanced-cache"
            )
        
        # Assert
        assert result1["metadata"]["strategy"] == "enhanced", \
            f"Expected enhanced strategy, got {result1['metadata']['strategy']}"
        
        # THE KEY ASSERTION - This should FAIL with current implementation
        assert result2["metadata"].get("cached") == True, \
            "Enhanced strategy response should be cached on second call"
        
        # Verify AI was only called ONCE (second call from cache)
        assert mock_agent.generate.call_count == 1, \
            f"AI should be called once, but was called {mock_agent.generate.call_count} times"

    @pytest.mark.asyncio
    async def test_direct_strategy_still_cached(self):
        """
        Test: Direct strategy should still be cached (existing behavior).
        This is a regression test to ensure we don't break existing caching.
        """
        # Arrange
        from app.services.orchestrator.orchestrator import IntelligentOrchestrator
        
        mock_memory_service = Mock()
        mock_memory_service.search_facts = AsyncMock(return_value=[
            {"text": "User's name is Denis", "importance": 0.95, "confidence": 0.95}
        ])
        mock_memory_service.add_facts = AsyncMock()
        
        mock_agent_factory = Mock()
        
        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory
        )
        
        # Mock high coverage (triggers direct)
        mock_eval = Mock()
        mock_eval.coverage_score = 0.95
        mock_eval.confidence = 0.9
        mock_eval.relevant_facts = [{"text": "User's name is Denis", "importance": 0.95}]
        mock_eval.gaps = []
        mock_eval.has_sufficient_coverage = True
        
        with patch.object(orchestrator.memory_evaluator, 'evaluate', new_callable=AsyncMock) as mock_evaluate:
            mock_evaluate.return_value = mock_eval
            
            # Act
            result1 = await orchestrator.process_query(
                query="What is my name?",
                session_id="test-direct-cache"
            )
            
            result2 = await orchestrator.process_query(
                query="What is my name?",
                session_id="test-direct-cache"
            )
        
        # Assert
        assert result1["metadata"]["strategy"] == "direct"
        assert result2["metadata"].get("cached") == True, \
            "Direct strategy should remain cached"

    @pytest.mark.asyncio
    async def test_deep_reasoning_not_cached(self):
        """
        Test: Deep reasoning responses should NOT be cached.
        These need fresh data from web search, etc.
        """
        # Arrange
        from app.services.orchestrator.orchestrator import IntelligentOrchestrator
        
        mock_memory_service = Mock()
        mock_memory_service.search_facts = AsyncMock(return_value=[])
        mock_memory_service.add_facts = AsyncMock()
        
        mock_agent = Mock()
        mock_agent.generate = AsyncMock(return_value={
            "response": "Deep analysis of AI trends",
            "status": "success"
        })
        
        mock_agent_factory = Mock()
        mock_agent_factory.create_agent = Mock(return_value=mock_agent)
        
        mock_web_search = AsyncMock()
        mock_web_search.search = AsyncMock(return_value=[
            {"title": "Latest AI News", "snippet": "AI is evolving..."}
        ])
        
        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory,
            web_search_service=mock_web_search
        )
        
        # Mock low coverage (triggers deep reasoning)
        mock_eval = Mock()
        mock_eval.coverage_score = 0.3  # Low coverage
        mock_eval.confidence = 0.4
        mock_eval.relevant_facts = []
        mock_eval.gaps = ["no information available"]
        mock_eval.has_sufficient_coverage = False
        
        with patch.object(orchestrator.memory_evaluator, 'evaluate', new_callable=AsyncMock) as mock_evaluate:
            mock_evaluate.return_value = mock_eval
            
            # Act
            result1 = await orchestrator.process_query(
                query="What are the latest trends in AI research?",
                session_id="test-deep-no-cache"
            )
            
            result2 = await orchestrator.process_query(
                query="What are the latest trends in AI research?",
                session_id="test-deep-no-cache"
            )
        
        # Assert
        assert result1["metadata"]["strategy"] == "deep_reasoning"
        
        # Deep reasoning should NOT be cached (needs fresh data)
        assert result2["metadata"].get("cached") != True, \
            "Deep reasoning should NOT be cached - needs fresh web search data"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
