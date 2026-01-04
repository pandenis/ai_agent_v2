"""
Tests for /api/v1/orchestrate endpoint

TDD Step 2: Test the orchestrate endpoint that uses IntelligentOrchestrator.

These tests verify:
1. Endpoint exists and accepts POST requests
2. Request validation works
3. Returns proper response structure
4. Security validation applied
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


# ==========================================
# Test 1: Endpoint exists
# ==========================================

def test_orchestrate_endpoint_exists():
    """
    Test: /api/v1/orchestrate endpoint exists

    Expected: POST request doesn't return 404
    """
    client = TestClient(app)

    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "What is my name?",
            "session_id": "test-session-123"
        }
    )

    # Should not be 404 (endpoint exists)
    # May be 500 if orchestrator fails, but not 404
    assert response.status_code != 404


# ==========================================
# Test 2: Request validation - missing query
# ==========================================

def test_orchestrate_rejects_missing_query():
    """
    Test: Endpoint rejects request without query

    Expected: 422 Unprocessable Entity
    """
    client = TestClient(app)

    response = client.post(
        "/api/v1/orchestrate",
        json={
            "session_id": "test-session-123"
            # Missing "query"
        }
    )

    assert response.status_code == 422


# ==========================================
# Test 3: Request validation - missing session_id
# ==========================================

def test_orchestrate_rejects_missing_session_id():
    """
    Test: Endpoint rejects request without session_id

    Expected: 422 Unprocessable Entity
    """
    client = TestClient(app)

    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "What is my name?"
            # Missing "session_id"
        }
    )

    assert response.status_code == 422


# ==========================================
# Test 4: Request validation - empty query
# ==========================================

def test_orchestrate_rejects_empty_query():
    """
    Test: Endpoint rejects empty query string

    Expected: 422 Unprocessable Entity (Pydantic validation)
    """
    client = TestClient(app)

    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "",
            "session_id": "test-session-123"
        }
    )

    assert response.status_code == 422


# ==========================================
# Test 5: Security - malicious input rejected
# ==========================================

def test_orchestrate_rejects_malicious_input():
    """
    Test: Endpoint rejects potentially malicious input

    Expected: 400 Bad Request for SQL injection attempt
    """
    client = TestClient(app)

    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "'; DROP TABLE users; --",
            "session_id": "test-session-123"
        }
    )

    assert response.status_code == 400


# ==========================================
# Test 6: Response structure
# ==========================================

@pytest.mark.asyncio
async def test_orchestrate_response_structure():
    """
    Test: Response has correct structure

    Expected: Response contains text and metadata
    """
    from httpx import ASGITransport, AsyncClient
    from app.api.deps import get_orchestrator

    mock_response = {
        "text": "Your name is Denis.",
        "metadata": {
            "strategy": "direct",
            "confidence": 0.95,
            "sources": ["memory"],
            "elapsed_time_ms": 50.0,
            "cost_usd": 0.0
        }
    }

    # Create mock orchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.process_query = AsyncMock(return_value=mock_response)

    # Override FastAPI dependency
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
                    "query": "What is my name?",
                    "session_id": "test-session-123"
                }
            )

        # Check structure
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "metadata" in data
        assert "strategy" in data["metadata"]
    finally:
        # Clean up override
        app.dependency_overrides.clear()


# ==========================================
# Test 7: use_chains parameter
# ==========================================

@pytest.mark.asyncio
async def test_orchestrate_accepts_use_chains_parameter():
    """
    Test: Endpoint accepts optional use_chains parameter

    Expected: Request with use_chains=true is accepted
    """
    from httpx import ASGITransport, AsyncClient
    from app.api.deps import get_orchestrator

    mock_response = {
        "text": "Response via chains",
        "metadata": {
            "strategy": "enhanced",
            "confidence": 0.85,
            "sources": ["memory", "ai"],
            "elapsed_time_ms": 150.0,
            "cost_usd": 0.0003
        }
    }

    # Create mock orchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.process_query = AsyncMock(return_value=mock_response)

    # Override FastAPI dependency
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
                    "query": "Compare Python and JavaScript",
                    "session_id": "test-session-123",
                    "use_chains": True
                }
            )

        assert response.status_code == 200

        # Verify use_chains was passed to orchestrator
        mock_orchestrator.process_query.assert_called_once()
        call_kwargs = mock_orchestrator.process_query.call_args[1]
        assert call_kwargs.get("use_chains") == True
    finally:
        # Clean up override
        app.dependency_overrides.clear()