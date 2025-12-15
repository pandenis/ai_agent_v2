"""
End-to-End Tests for Intelligent Orchestrator

These tests verify that all components work together correctly:
1. QueryAnalyzer → MemoryEvaluator → DecisionEngine → Response
2. All three strategies work (direct, enhanced, deep_reasoning)
3. Memory updates after responses
4. Error handling works
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from app.services.orchestrator.orchestrator import IntelligentOrchestrator
from app.services.orchestrator.query_analyzer import QueryAnalysis
from app.services.orchestrator.memory_evaluator import MemoryEvaluation
from app.services.orchestrator.decision_engine import ResponseStrategy


# ==========================================
# Test Fixtures (Setup)
# ==========================================

@pytest.fixture
def mock_memory_service():
    """Create a mock memory service for testing"""
    service = AsyncMock()

    # Default: return empty facts
    service.search_facts = AsyncMock(return_value=[])
    service.add_fact = AsyncMock(return_value=True)

    return service


@pytest.fixture
def mock_agent():
    """Create a mock AI agent"""
    agent = AsyncMock()
    agent.name = "test-agent"
    agent.process = AsyncMock(return_value="This is a test AI response")
    return agent


@pytest.fixture
def mock_agent_registry(mock_agent):
    """Create a mock agent registry"""
    registry = Mock()
    registry.get_agent = Mock(return_value=mock_agent)
    registry.get_default_agent = Mock(return_value=mock_agent)
    return registry


@pytest.fixture
def mock_fact_extractor():
    """Create a mock fact extractor"""
    extractor = AsyncMock()
    extractor.extract_facts = AsyncMock(return_value=[
        {
            "text": "Test fact",
            "importance": 0.8,
            "confidence": 0.9
        }
    ])
    return extractor


@pytest.fixture
def orchestrator(mock_memory_service, mock_agent_registry, mock_fact_extractor):
    """Create an orchestrator instance for testing"""
    return IntelligentOrchestrator(
        memory_service=mock_memory_service,
        agent_registry=mock_agent_registry,
        fact_extractor=mock_fact_extractor
    )


# ==========================================
# Test 1: Simple Query → Direct Answer
# ==========================================

@pytest.mark.asyncio
async def test_simple_query_direct_answer(orchestrator, mock_memory_service):
    """
    Test Case: Simple question with answer in memory

    Scenario:
        User asks: "What is my name?"
        Memory has: "User's name is Denis"
        Expected: Direct answer from memory (no AI needed)
    """
    # Setup: Memory has the answer
    mock_memory_service.search_facts.return_value = [
        {"text": "User's name is Denis", "importance": 0.9, "confidence": 0.95},
        {"text": "User is Denis", "importance": 0.9, "confidence": 0.95},
        {"text": "Denis is the user's name", "importance": 0.9, "confidence": 0.95},
        {"text": "The user is called Denis", "importance": 0.9, "confidence": 0.95},
        {"text": "User's full name is Denis", "importance": 0.9, "confidence": 0.95}

    ]

    # Execute: Process the query
    result = await orchestrator.process_query(
        query="What is my name?",
        session_id="test-session-001"
    )

    # Verify: Response structure
    assert "text" in result
    assert "metadata" in result

    # Verify: Used direct strategy (fastest, cheapest)
    assert result["metadata"]["strategy"] == "direct"
    assert result["metadata"]["cost_usd"] == 0.0
    assert "memory" in result["metadata"]["sources"]

    # Verify: Response contains the answer
    assert "Denis" in result["text"]

    # Verify: Fast response (direct answers should be < 100ms)
    assert result["metadata"]["elapsed_time_ms"] < 100

    print("✅ Test 1 PASSED: Simple query with direct answer")


# ==========================================
# Test 2: Medium Query → Enhanced Answer
# ==========================================

@pytest.mark.asyncio
async def test_medium_query_enhanced_answer(orchestrator, mock_memory_service, mock_agent):
    """
    Test Case: Medium complexity question needs AI + memory

    Scenario:
        User asks: "What programming languages should I learn?"
        Memory has: Some context about user's interests
        Expected: AI response enhanced with memory context
    """
    # Setup: Memory has partial context
    mock_memory_service.search_facts.return_value = [
        {
            "text": "User is a QA Engineer",
            "importance": 0.8,
            "confidence": 0.9
        },
        {
            "text": "User loves Python",
            "importance": 0.7,
            "confidence": 0.85
        }
    ]

    # Setup: Mock AI response
    mock_agent.process.return_value = "Based on your Python skills and QA background, I recommend learning JavaScript for web automation."

    # Execute: Process the query
    result = await orchestrator.process_query(
        query="What programming languages should I learn next?",
        session_id="test-session-002"
    )

    # Verify: Used enhanced strategy (AI + memory)
    assert result["metadata"]["strategy"] == "enhanced"
    assert result["metadata"]["cost_usd"] > 0  # AI costs money
    assert "memory" in result["metadata"]["sources"]
    assert "test-agent" in result["metadata"]["sources"]

    # Verify: AI was called with memory context
    mock_agent.process.assert_called_once()
    call_args = mock_agent.process.call_args[0][0]
    assert "User is a QA Engineer" in call_args  # Memory context included
    assert "What programming languages" in call_args  # Original query included

    # Verify: Response makes sense
    assert len(result["text"]) > 20  # Substantial response

    print("✅ Test 2 PASSED: Medium query with enhanced answer")


# ==========================================
# Test 3: Complex Query → Deep Reasoning
# ==========================================

@pytest.mark.asyncio
async def test_complex_query_deep_reasoning(orchestrator, mock_memory_service, mock_agent):
    """
    Test Case: Complex question needs deep AI reasoning

    Scenario:
        User asks: "Compare quantum computing with classical computing"
        Memory has: Little relevant info
        Expected: Deep reasoning with premium AI
    """
    # Setup: Memory has very little
    mock_memory_service.search_facts.return_value = []

    # Setup: Mock comprehensive AI response
    mock_agent.process.return_value = """
    Quantum computing and classical computing differ fundamentally:
    1. Classical computers use bits (0 or 1)
    2. Quantum computers use qubits (superposition of 0 and 1)
    [... comprehensive explanation ...]
    """

    # Execute: Process the query
    result = await orchestrator.process_query(
        query="Compare quantum computing with classical computing and explain when each is better",
        session_id="test-session-003"
    )

    # Verify: Used deep reasoning strategy
    assert result["metadata"]["strategy"] == "deep_reasoning"
    assert result["metadata"]["reasoning_depth"] >= 2
    assert result["metadata"]["cost_usd"] > 0

    # Verify: Used premium model
    assert "deep_reasoning" in result["metadata"]["sources"]

    # Verify: Comprehensive response
    assert len(result["text"]) > 100  # Should be detailed

    print("✅ Test 3 PASSED: Complex query with deep reasoning")


# ==========================================
# Test 4: Memory Updates After Response
# ==========================================

@pytest.mark.asyncio
async def test_memory_update_after_response(
        orchestrator,
        mock_memory_service,
        mock_fact_extractor
):
    """
    Test Case: Facts are extracted and saved after each response

    Scenario:
        User: "I live in Tel Aviv"
        Expected: Fact "User lives in Tel Aviv" saved to memory
    """
    # Setup: Fresh memory
    mock_memory_service.search_facts.return_value = []

    # Setup: Fact extractor finds new fact
    mock_fact_extractor.extract_facts.return_value = [
        {
            "text": "User lives in Tel Aviv",
            "importance": 0.85,
            "confidence": 0.9,
            "fact_type": "location"
        }
    ]

    # Execute: Process the query
    result = await orchestrator.process_query(
        query="I live in Tel Aviv and work as a QA Engineer",
        session_id="test-session-004"
    )

    # Verify: Fact extraction was called
    mock_fact_extractor.extract_facts.assert_called_once()

    # Verify: Facts were saved to memory
    assert mock_memory_service.add_fact.called
    call_count = mock_memory_service.add_fact.call_count
    assert call_count >= 1  # At least one fact saved

    print("✅ Test 4 PASSED: Memory updated after response")


# ==========================================
# Test 5: Error Handling
# ==========================================

@pytest.mark.asyncio
async def test_error_handling(orchestrator, mock_agent):
    """
    Test Case: Graceful error handling when something fails

    Scenario:
        AI agent throws an error
        Expected: Safe error response returned to user
    """
    # Setup: Make agent fail
    mock_agent.process.side_effect = Exception("AI service unavailable")

    # Execute: Process the query (should not crash)
    result = await orchestrator.process_query(
        query="Test query that will fail",
        session_id="test-session-005"
    )

    # Verify: Error response structure
    assert "text" in result
    assert "metadata" in result
    assert result["metadata"]["strategy"] == "error"

    # Verify: User gets friendly error message
    assert "error" in result["text"].lower() or "apolog" in result["text"].lower()

    # Verify: Error details in metadata
    assert "error" in result["metadata"]

    print("✅ Test 5 PASSED: Error handled gracefully")


# ==========================================
# Test 6: No Memory, No AI (Edge Case)
# ==========================================

@pytest.mark.asyncio
async def test_no_memory_no_ai(orchestrator, mock_memory_service, mock_agent_registry):
    """
    Test Case: What happens when we have no memory and no AI?

    Scenario:
        Empty memory
        No AI agents available
        Expected: Graceful fallback response
    """
    # Setup: Empty memory
    mock_memory_service.search_facts.return_value = []

    # Setup: No agents available
    mock_agent_registry.get_agent.return_value = None
    mock_agent_registry.get_default_agent.return_value = None

    # Execute: Process the query
    result = await orchestrator.process_query(
        query="Tell me about Python",
        session_id="test-session-006"
    )

    # Verify: Returns something (doesn't crash)
    assert "text" in result
    assert len(result["text"]) > 0

    # Verify: Indicates limitation
    # Verify: Indicates limitation (accepts various error messages)
    assert ("don't have" in result["text"].lower() or
            "information" in result["text"].lower() or
            "apologize" in result["text"].lower() or
            "need a more powerful" in result["text"].lower())

    print("✅ Test 6 PASSED: Graceful fallback when no resources")


# ==========================================
# Test 7: Performance Metrics
# ==========================================

@pytest.mark.asyncio
async def test_performance_metrics(orchestrator):
    """
    Test Case: Verify all performance metrics are tracked

    Scenario:
        Any query
        Expected: Metadata contains timing, cost, sources
    """
    # Execute: Process the query
    result = await orchestrator.process_query(
        query="Test query",
        session_id="test-session-007"
    )

    # Verify: All required metrics present
    metadata = result["metadata"]

    assert "strategy" in metadata
    assert "confidence" in metadata
    assert "sources" in metadata
    assert "elapsed_time_ms" in metadata
    assert "cost_usd" in metadata
    assert "reasoning_depth" in metadata
    assert "memory_coverage" in metadata

    # Verify: Metric types
    assert isinstance(metadata["elapsed_time_ms"], (int, float))
    assert isinstance(metadata["cost_usd"], (int, float))
    assert isinstance(metadata["confidence"], (int, float))
    assert isinstance(metadata["sources"], list)

    # Verify: Reasonable values
    assert metadata["elapsed_time_ms"] >= 0
    assert metadata["cost_usd"] >= 0
    assert 0 <= metadata["confidence"] <= 1
    assert 0 <= metadata["memory_coverage"] <= 1

    print("✅ Test 7 PASSED: Performance metrics tracked correctly")


# ==========================================
# Test 8: End-to-End Flow (Complete Scenario)
# ==========================================

@pytest.mark.asyncio
async def test_complete_e2e_flow(
        orchestrator,
        mock_memory_service,
        mock_agent,
        mock_fact_extractor
):
    """
    Test Case: Complete end-to-end flow through all stages

    Scenario:
        1. User asks question
        2. Query analyzed
        3. Memory checked
        4. Strategy decided
        5. Response generated
        6. Memory updated
        7. Response returned
    """
    # Setup: Memory has some context
    mock_memory_service.search_facts.return_value = [
        {"text": "User is Denis", "importance": 0.9}
    ]

    # Setup: AI provides response
    mock_agent.process.return_value = "Hello Denis! How can I help you today?"

    # Setup: New facts extracted
    mock_fact_extractor.extract_facts.return_value = [
        {"text": "User greeted the system", "importance": 0.3}
    ]

    # Execute: Complete flow
    result = await orchestrator.process_query(
        query="Hello! Can you help me?",
        session_id="test-session-008"
    )

    # Verify: All stages executed
    # 1. Query Analysis (implicit - no error)
    assert result is not None

    # 2. Memory Search (was called)
    assert mock_memory_service.search_facts.called

    # 3. Response Generated
    assert result["text"]
    assert len(result["text"]) > 0

    # 4. Memory Updated
    assert mock_fact_extractor.extract_facts.called

    # 5. Complete metadata
    assert all(key in result["metadata"] for key in [
        "strategy", "confidence", "sources", "elapsed_time_ms", "cost_usd"
    ])

    print("✅ Test 8 PASSED: Complete E2E flow works")


# ==========================================
# Test Summary Function
# ==========================================

def test_summary():
    """
    Print a summary of what we're testing.
    This helps understand test coverage.
    """
    print("\n" + "=" * 60)
    print("ORCHESTRATOR E2E TEST SUITE SUMMARY")
    print("=" * 60)
    print("\nTest Coverage:")
    print("  ✅ Test 1: Simple Query → Direct Answer")
    print("  ✅ Test 2: Medium Query → Enhanced Answer")
    print("  ✅ Test 3: Complex Query → Deep Reasoning")
    print("  ✅ Test 4: Memory Updates")
    print("  ✅ Test 5: Error Handling")
    print("  ✅ Test 6: Fallback Scenarios")
    print("  ✅ Test 7: Performance Metrics")
    print("  ✅ Test 8: Complete E2E Flow")
    print("\nTotal: 8 comprehensive E2E tests")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # If running this file directly, show the summary
    test_summary()