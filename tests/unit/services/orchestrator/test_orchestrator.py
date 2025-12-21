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
            "importance": 0.5,
            "confidence": 0.9
        },
        {
            "text": "User loves Python",
            "importance": 0.4,
            "confidence": 0.5
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
    print("  ✅ Test 9: ResponseFormatter Integration")  # NEW!
    print("\nTotal: 9 comprehensive E2E tests")
    print("=" * 60 + "\n")

# ==========================================
# Test 9: ResponseFormatter Integration
# ==========================================

@pytest.mark.asyncio
async def test_response_formatter_integration(
        orchestrator,
        mock_memory_service,
        mock_agent
):
    """
    Test Case: ResponseFormatter is used to format all responses

    Scenario:
        Verify that responses are properly formatted using ResponseFormatter
        for all three strategies: direct, enhanced, deep_reasoning
    """
    from app.services.orchestrator.response_formatter import ResponseFormatter

    # Verify: ResponseFormatter is initialized in orchestrator
    assert hasattr(orchestrator, 'response_formatter')
    assert isinstance(orchestrator.response_formatter, ResponseFormatter)

    # Test 1: Direct answer formatting
    # Setup: High-confidence, highly relevant facts for direct answer
    mock_memory_service.search_facts.return_value = [
        {"text": "User's name is Denis", "importance": 0.95, "confidence": 0.98, "fact_type": "personal"},
        {"text": "Denis is the user", "importance": 0.94, "confidence": 0.97, "fact_type": "personal"},
        {"text": "User goes by Denis", "importance": 0.93, "confidence": 0.96, "fact_type": "personal"},
        {"text": "Denis is what user is called", "importance": 0.92, "confidence": 0.95, "fact_type": "personal"},
        {"text": "The name Denis belongs to user", "importance": 0.91, "confidence": 0.94, "fact_type": "personal"}
    ]

    result = await orchestrator.process_query(
        query="What is my name?",
        session_id="test-formatter-001"
    )

    # Response should be formatted and contain answer
    assert "Denis" in result["text"]
    assert len(result["text"]) > 10
    # Bullet list format (multiple facts) or sentence format (single fact)
    assert "•" in result["text"] or "." in result["text"]

    print(f"  Test 1: Strategy used = {result['metadata']['strategy']}")

    # Test 2: Enhanced answer formatting
    mock_memory_service.search_facts.return_value = [
        {"text": "User knows Python", "importance": 0.8, "confidence": 0.9, "fact_type": "skill"},
        {"text": "User is a QA Engineer", "importance": 0.75, "confidence": 0.85, "fact_type": "professional"}
    ]

    mock_agent.process.return_value = "Based on your Python skills, I recommend trying JavaScript."

    result = await orchestrator.process_query(
        query="What programming language should I learn next?",
        session_id="test-formatter-002"
    )

    # Should format the response (strategy may vary)
    assert len(result["text"]) > 0
    # Response should contain either AI response or context
    assert "Python" in result["text"] or "JavaScript" in result["text"] or "QA Engineer" in result["text"]

    print(f"  Test 2: Strategy used = {result['metadata']['strategy']}")


@pytest.mark.asyncio
async def test_direct_answer_no_facts_falls_back_to_ai(
        orchestrator, mock_memory_service, mock_agent
):
    """
    Test Case: Query with NO facts in memory
    Expected: Falls back to deep_reasoning (AI) when no memory coverage
    """
    # Setup: No facts in memory → coverage = 0
    mock_memory_service.search_facts.return_value = []
    mock_agent.process.return_value = "I don't know your name yet. Could you tell me?"

    # Execute with simple query
    result = await orchestrator.process_query(
        query="What is my name?",
        session_id="test-no-facts"
    )

    # Assert: With 0 coverage, falls back to deep_reasoning (AI)
    assert result["metadata"]["strategy"] == "deep_reasoning"
    assert result is not None
    assert len(result["text"]) > 0

@pytest.mark.asyncio
async def test_memory_update_failure_doesnt_break_response(
        orchestrator, mock_memory_service, mock_agent
):
    """
    Test Case: Memory update fails but response should still work
    Expected: Response returns successfully despite memory failure
    """
    # Setup: Facts for query
    mock_memory_service.search_facts.return_value = [
        {"text": "User likes Python", "importance": 0.5, "confidence": 0.5}
    ]
    mock_agent.process.return_value = "Python is a great language!"

    # Setup: Memory update fails
    mock_memory_service.add_fact.side_effect = Exception("Database connection error")

    # Execute
    result = await orchestrator.process_query(
        query="Tell me about Python",
        session_id="test-memory-failure"
    )

    # Assert: Response should still be returned despite memory failure
    assert result is not None
    assert "text" in result
    assert len(result["text"]) > 0


@pytest.mark.asyncio
async def test_enhanced_fallback_when_no_agent_available(
        mock_memory_service, mock_agent
):
    """
    Test Case: Enhanced strategy but no agent available
    Expected: Falls back to direct answer from memory
    """
    from app.services.orchestrator.orchestrator import IntelligentOrchestrator
    from app.services.orchestrator.response_formatter import ResponseFormatter
    from unittest.mock import Mock

    # Create registry that returns None (no agent available)
    mock_registry_no_agent = Mock()
    mock_registry_no_agent.get_agent = Mock(return_value=None)
    mock_registry_no_agent.get_default_agent = Mock(return_value=None)

    # Create orchestrator with no-agent registry
    orchestrator_no_agent = IntelligentOrchestrator(
        memory_service=mock_memory_service,
        agent_registry=mock_registry_no_agent
    )

    # Setup: Medium coverage (triggers enhanced) but with facts
    mock_memory_service.search_facts.return_value = [
        {"text": "User knows Python programming", "importance": 0.5, "confidence": 0.5},
        {"text": "User is a developer", "importance": 0.5, "confidence": 0.5}
    ]

    # Execute: Medium query that would trigger enhanced
    result = await orchestrator_no_agent.process_query(
        query="What programming skills do I have?",
        session_id="test-no-agent"
    )

    # Assert: Should fallback to memory-based answer
    assert result is not None
    assert "text" in result
    # Should contain info from facts since agent was unavailable
    assert "Python" in result["text"] or "developer" in result["text"]


@pytest.mark.asyncio
async def test_direct_answer_method_with_empty_facts(
        orchestrator, mock_memory_service
):
    """
    Test Case: _direct_answer called with empty facts list
    Expected: Returns default 'no information' message
    """
    # Call _direct_answer directly with empty list
    result = orchestrator._direct_answer([])

    # Assert: Should return default message
    assert "don't have" in result.lower() or "information" in result.lower()


@pytest.mark.asyncio
async def test_build_context_sorts_by_importance(orchestrator):
    """
    Test Case: Context building should prioritize important facts
    Expected: High-importance facts appear first in context
    """
    # Arrange: Facts with varying importance (out of order)
    facts = [
        {"text": "Low importance fact", "importance": 0.3, "confidence": 0.8},
        {"text": "High importance fact", "importance": 0.95, "confidence": 0.9},
        {"text": "Medium importance fact", "importance": 0.6, "confidence": 0.85},
    ]

    # Act: Build context
    context = orchestrator._build_context(facts)

    # Assert: High importance fact should come first
    high_pos = context.find("High importance")
    medium_pos = context.find("Medium importance")
    low_pos = context.find("Low importance")

    assert high_pos < medium_pos < low_pos, \
        "Facts should be sorted by importance (highest first)"

@pytest.mark.asyncio
async def test_enhanced_answer_uses_sorted_context(
        orchestrator, mock_memory_service, mock_agent
):
    """
    Test Case: Enhanced answer should use _build_context for sorted facts
    Expected: High-importance facts are prioritized in AI prompt
    """
    # Setup: Facts with varying importance (unsorted)
    mock_memory_service.search_facts.return_value = [
        {"text": "Low priority info", "importance": 0.2, "confidence": 0.8},
        {"text": "Critical user preference", "importance": 0.95, "confidence": 0.9},
        {"text": "Medium relevance fact", "importance": 0.5, "confidence": 0.85},
    ]

    # Capture what prompt is sent to AI
    captured_prompt = None

    async def capture_process(prompt):
        nonlocal captured_prompt
        captured_prompt = prompt
        return "AI response based on context"

    mock_agent.process = capture_process

    # Execute
    result = await orchestrator.process_query(
        query="What do you know about my preferences?",
        session_id="test-sorted-context"
    )

    # Assert: Critical fact should appear before low priority in context
    assert captured_prompt is not None
    critical_pos = captured_prompt.find("Critical user preference")
    low_pos = captured_prompt.find("Low priority info")

    # Critical should come first (or low might not be included at all)
    assert critical_pos < low_pos or low_pos == -1, \
        "High-importance facts should appear first in context"


@pytest.mark.asyncio
async def test_deep_reasoning_uses_sorted_context(
        orchestrator, mock_memory_service, mock_agent
):
    """
    Test Case: Deep reasoning should use _build_context for sorted facts
    Expected: High-importance facts appear first in comprehensive context
    """
    # Setup: Facts with varying importance (unsorted)
    mock_memory_service.search_facts.return_value = [
        {"text": "Minor detail", "importance": 0.1, "confidence": 0.7},
        {"text": "Crucial background info", "importance": 0.98, "confidence": 0.95},
        {"text": "Somewhat relevant fact", "importance": 0.4, "confidence": 0.8},
    ]

    # Capture what prompt is sent to AI
    captured_prompt = None

    async def capture_process(prompt):
        nonlocal captured_prompt
        captured_prompt = prompt
        return "Deep analysis response with multiple paragraphs."

    mock_agent.process = capture_process

    # Execute: Complex query triggers deep reasoning
    result = await orchestrator.process_query(
        query="Compare and analyze the pros and cons of different approaches",
        session_id="test-deep-sorted"
    )

    # Assert: Crucial info should appear before minor detail
    assert captured_prompt is not None
    crucial_pos = captured_prompt.find("Crucial background info")
    minor_pos = captured_prompt.find("Minor detail")

    assert crucial_pos < minor_pos or minor_pos == -1, \
        "High-importance facts should appear first in deep reasoning context"


@pytest.mark.asyncio
async def test_orchestrator_tracks_metrics(
        orchestrator, mock_memory_service, mock_agent
):
    """
    Test Case: Orchestrator should track query metrics
    Expected: Metrics recorded after each query
    """
    # Setup
    mock_memory_service.search_facts.return_value = [
        {"text": "Test fact", "importance": 0.9, "confidence": 0.9}
    ]
    mock_agent.process.return_value = "Test response"

    # Execute multiple queries
    await orchestrator.process_query(query="What is my name?", session_id="test-1")
    await orchestrator.process_query(query="Tell me about Python", session_id="test-2")

    # Assert: Metrics should be tracked
    assert hasattr(orchestrator, 'metrics'), "Orchestrator should have metrics attribute"
    stats = orchestrator.metrics.get_stats()
    assert stats["total_queries"] == 2, "Should track 2 queries"


@pytest.mark.asyncio
async def test_deep_reasoning_uses_reasoning_planner(
        orchestrator, mock_memory_service, mock_agent
):
    """
    Test Case: Deep reasoning should use ReasoningPlanner
    Expected: Plan is created and steps are executed
    """
    # Setup: Low coverage to trigger deep reasoning
    mock_memory_service.search_facts.return_value = [
        {"text": "User interested in travel", "importance": 0.3, "confidence": 0.5}
    ]
    mock_agent.process.return_value = "Comprehensive analysis of Tokyo vs Paris costs..."

    # Execute: Complex query triggers deep reasoning
    result = await orchestrator.process_query(
        query="Compare the cost of living between Tokyo and Paris with cultural factors",
        session_id="test-planner"
    )

    # Assert: Should use deep_reasoning strategy
    assert result["metadata"]["strategy"] == "deep_reasoning"
    # Assert: Should have reasoning_steps in metadata (from planner)
    assert "reasoning_steps" in result["metadata"], \
        "Deep reasoning should include reasoning_steps from planner"
    assert len(result["metadata"]["reasoning_steps"]) >= 2

if __name__ == "__main__":
    # If running this file directly, show the summary
    test_summary()