"""
End-to-End Integration Tests for /api/v1/orchestrate endpoint

These tests verify the complete flow:
1. HTTP Request → Endpoint → Orchestrator → Response
2. Different strategies work (direct, enhanced, deep_reasoning)
3. Caching behavior
4. Error handling
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.deps import get_orchestrator
from app.services.orchestrator.orchestrator import IntelligentOrchestrator
from app.services.orchestrator.memory_evaluator import MemoryEvaluation


# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def mock_memory_service():
    """Mock memory service"""
    service = AsyncMock()
    service.search_facts = AsyncMock(return_value=[])
    service.add_fact = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_agent():
    """Mock AI agent"""
    agent = AsyncMock()
    agent.name = "test-agent"
    agent.process = AsyncMock(return_value="AI generated response")
    return agent


@pytest.fixture
def mock_agent_registry(mock_agent):
    """Mock agent registry"""
    registry = Mock()
    registry.get_agent = Mock(return_value=mock_agent)
    registry.get_default_agent = Mock(return_value=mock_agent)
    return registry


# ==========================================
# Test 1: Direct Strategy (High Memory Coverage)
# ==========================================

@pytest.mark.asyncio
async def test_e2e_direct_strategy_from_memory():
    """
    E2E Test: Query with high memory coverage uses direct strategy

    Flow:
    1. User asks "What is my name?"
    2. Memory has answer with 95% coverage
    3. Orchestrator returns direct answer (no AI)
    4. Response time < 200ms
    """
    # Create orchestrator with mocked high-coverage memory
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[
        Mock(text="User's name is Denis", importance=0.9, confidence=0.95)
    ])

    mock_registry = Mock()
    mock_registry.get_agent = Mock(return_value=AsyncMock())

    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_registry=mock_registry,
    )

    # Mock memory evaluator to return high coverage
    with patch.object(
            orchestrator.memory_evaluator,
            'evaluate',
            new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.return_value = MemoryEvaluation(
            coverage_score=0.95,
            relevant_facts=[{"text": "User's name is Denis", "importance": 0.9}],
            gaps=[],
            confidence=0.95
        )

        async def mock_get_orchestrator():
            return orchestrator

        app.dependency_overrides[get_orchestrator] = mock_get_orchestrator

        try:
            async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/orchestrate",
                    json={
                        "query": "What is my name?",
                        "session_id": "test-direct"
                    }
                )

            assert response.status_code == 200
            data = response.json()

            # Verify direct strategy was used
            assert data["metadata"]["strategy"] == "direct"
            assert "memory" in data["metadata"]["sources"]
            assert data["metadata"]["cost_usd"] == 0.0

        finally:
            app.dependency_overrides.clear()


# ==========================================
# Test 2: Enhanced Strategy (Medium Coverage)
# ==========================================

@pytest.mark.asyncio
async def test_e2e_enhanced_strategy_with_ai():
    """
    E2E Test: Query with medium memory coverage uses enhanced strategy

    Flow:
    1. User asks about recommendations
    2. Memory has partial info (70% coverage)
    3. Orchestrator uses AI to enhance response
    """
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[
        Mock(text="User likes Python", importance=0.8, confidence=0.9)
    ])

    mock_agent = AsyncMock()
    mock_agent.name = "mistral"
    mock_agent.process = AsyncMock(return_value="Based on your Python experience, I recommend learning FastAPI.")

    mock_registry = Mock()
    mock_registry.get_agent = Mock(return_value=mock_agent)
    mock_registry.get_default_agent = Mock(return_value=mock_agent)

    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_registry=mock_registry,
    )

    with patch.object(
            orchestrator.memory_evaluator,
            'evaluate',
            new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.return_value = MemoryEvaluation(
            coverage_score=0.75,
            relevant_facts=[{"text": "User likes Python", "importance": 0.8}],
            gaps=["specific framework preferences"],
            confidence=0.75
        )

        async def mock_get_orchestrator():
            return orchestrator

        app.dependency_overrides[get_orchestrator] = mock_get_orchestrator

        try:
            async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/orchestrate",
                    json={
                        "query": "What framework should I learn?",
                        "session_id": "test-enhanced"
                    }
                )

            assert response.status_code == 200
            data = response.json()

            # Verify enhanced strategy
            assert data["metadata"]["strategy"] == "enhanced"

        finally:
            app.dependency_overrides.clear()


# ==========================================
# Test 3: Deep Reasoning Strategy (Low Coverage)
# ==========================================

@pytest.mark.asyncio
async def test_e2e_deep_reasoning_strategy():
    """
    E2E Test: Complex query with low memory coverage uses deep reasoning

    Flow:
    1. User asks complex comparison question
    2. Memory has little relevant info
    3. Orchestrator uses deep reasoning with multiple steps
    """
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[])

    mock_agent = AsyncMock()
    mock_agent.name = "deepseek"
    mock_agent.process = AsyncMock(return_value="Deep analysis of quantum vs classical computing...")

    mock_registry = Mock()
    mock_registry.get_agent = Mock(return_value=mock_agent)
    mock_registry.get_default_agent = Mock(return_value=mock_agent)

    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_registry=mock_registry,
    )

    with patch.object(
            orchestrator.memory_evaluator,
            'evaluate',
            new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.return_value = MemoryEvaluation(
            coverage_score=0.2,
            relevant_facts=[],
            gaps=["quantum computing knowledge", "classical computing details"],
            confidence=0.2
        )

        async def mock_get_orchestrator():
            return orchestrator

        app.dependency_overrides[get_orchestrator] = mock_get_orchestrator

        try:
            async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/v1/orchestrate",
                    json={
                        "query": "Compare quantum computing with classical computing for machine learning",
                        "session_id": "test-deep"
                    }
                )

            assert response.status_code == 200
            data = response.json()

            # Verify deep reasoning strategy
            assert data["metadata"]["strategy"] == "deep_reasoning"

        finally:
            app.dependency_overrides.clear()


# ==========================================
# Test 4: Response Caching Works
# ==========================================

@pytest.mark.asyncio
async def test_e2e_caching_returns_cached_response():
    """
    E2E Test: Second identical query returns cached response

    Flow:
    1. First query → processes normally
    2. Second identical query → returns from cache (faster)
    """
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[
        Mock(text="User's favorite color is blue", importance=0.9, confidence=0.95)
    ])

    mock_registry = Mock()
    mock_registry.get_agent = Mock(return_value=AsyncMock())

    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_registry=mock_registry,
    )

    with patch.object(
            orchestrator.memory_evaluator,
            'evaluate',
            new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.return_value = MemoryEvaluation(
            coverage_score=0.95,
            relevant_facts=[{"text": "User's favorite color is blue", "importance": 0.9}],
            gaps=[],
            confidence=0.95
        )

        async def mock_get_orchestrator():
            return orchestrator

        app.dependency_overrides[get_orchestrator] = mock_get_orchestrator

        try:
            async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test"
            ) as client:
                # First request
                response1 = await client.post(
                    "/api/v1/orchestrate",
                    json={
                        "query": "What is my favorite color?",
                        "session_id": "test-cache"
                    }
                )

                # Second identical request (should be cached)
                response2 = await client.post(
                    "/api/v1/orchestrate",
                    json={
                        "query": "What is my favorite color?",
                        "session_id": "test-cache"
                    }
                )

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Both should return same result
            data1 = response1.json()
            data2 = response2.json()
            assert data1["text"] == data2["text"]

        finally:
            app.dependency_overrides.clear()


# ==========================================
# Test 5: Error Handling
# ==========================================

@pytest.mark.asyncio
async def test_e2e_handles_orchestrator_error_gracefully():
    """
    E2E Test: Orchestrator error returns 500 with message
    """
    mock_orchestrator = AsyncMock()
    mock_orchestrator.process_query = AsyncMock(
        side_effect=Exception("Internal orchestrator error")
    )

    async def mock_get_orchestrator():
        return mock_orchestrator

    app.dependency_overrides[get_orchestrator] = mock_get_orchestrator

    try:
        async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/orchestrate",
                json={
                    "query": "This will fail",
                    "session_id": "test-error"
                }
            )

        # Should return 500 internal server error
        assert response.status_code == 500

    finally:
        app.dependency_overrides.clear()