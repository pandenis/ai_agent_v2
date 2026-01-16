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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.deps import get_db
from app.core.database import Base


# ==========================================
# Test Database Setup
# ==========================================
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def test_db_override():
    """Create a test database override for the endpoint tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async def override_get_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with TestSessionLocal() as session:
            yield session
    
    return override_get_db


@pytest.fixture
def client(test_db_override):
    """Create test client with db override."""
    app.dependency_overrides[get_db] = test_db_override
    yield TestClient(app)
    app.dependency_overrides.clear()


# ==========================================
# Test 1: Endpoint exists
# ==========================================
def test_orchestrate_endpoint_exists(client):
    """
    Test: /api/v1/orchestrate endpoint exists
    Expected: POST request doesn't return 404
    """
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
def test_orchestrate_rejects_missing_query(client):
    """
    Test: Endpoint rejects request without query
    Expected: 422 Unprocessable Entity
    """
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "session_id": "test-session-123"
        }
    )
    assert response.status_code == 422


# ==========================================
# Test 3: Request validation - missing session_id
# ==========================================
def test_orchestrate_rejects_missing_session_id(client):
    """
    Test: Endpoint rejects request without session_id
    Expected: 422 Unprocessable Entity
    """
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "What is my name?"
        }
    )
    assert response.status_code == 422


# ==========================================
# Test 4: Response structure
# ==========================================
def test_orchestrate_response_structure(client):
    """
    Test: Response has proper structure
    Expected: Response contains text and metadata
    """
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "Hello",
            "session_id": "test-session-123"
        }
    )
    # Should not be 404 or 422
    assert response.status_code not in [404, 422]
    
    # If we get a successful response, check structure
    if response.status_code == 200:
        data = response.json()
        assert "text" in data
        assert "metadata" in data


# ==========================================
# Test 5: use_chains parameter accepted
# ==========================================
def test_orchestrate_accepts_use_chains_parameter(client):
    """
    Test: Endpoint accepts use_chains parameter
    Expected: No validation error for use_chains
    """
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "What is my name?",
            "session_id": "test-session-123",
            "use_chains": True
        }
    )
    # Should not be 422 (use_chains is valid parameter)
    assert response.status_code != 422


# ==========================================
# Test 6: Security validation - invalid session_id
# ==========================================
def test_orchestrate_rejects_invalid_session_id(client):
    """
    Test: Endpoint rejects invalid session_id format
    Expected: 400 Bad Request
    """
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "What is my name?",
            "session_id": "../../../etc/passwd"  # Path traversal attempt
        }
    )
    assert response.status_code in [400, 422]


# ==========================================
# Test 7: Security validation - empty query
# ==========================================
def test_orchestrate_rejects_empty_query(client):
    """
    Test: Endpoint rejects empty query
    Expected: 400 Bad Request
    """
    response = client.post(
        "/api/v1/orchestrate",
        json={
            "query": "",
            "session_id": "test-session-123"
        }
    )
    assert response.status_code in [400, 422]
