"""
Integration test fixtures and configuration.

This module provides:
- In-memory database for testing
- Mocked services (AgentService, MemoryService, Ollama)
- Test client with dependency overrides
- Sample data fixtures
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# Detect CI environment
IN_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """Create in-memory SQLite engine for testing."""
    from app.core.database import Base
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with mocked database."""
    from app.main import app
    from app.core.database import get_db
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_agent_response():
    """Standard mock response from agent."""
    return {
        "status": "success",
        "response": "This is a mocked AI response for testing purposes.",
        "agent_name": "mistral",
        "model": "mistral:7b-instruct",
        "tokens": 25
    }


@pytest.fixture
def mock_agent_service(mock_agent_response):
    """Mock AgentService for testing without real AI."""
    mock = MagicMock()
    mock.generate_response = AsyncMock(return_value=mock_agent_response)
    mock.get_agent_status = AsyncMock(return_value={
        "agents": {
            "mistral": {"enabled": True, "available": True, "type": "local_ollama"},
            "groq": {"enabled": True, "available": False, "type": "cloud_api"},
            "llama3": {"enabled": True, "available": True, "type": "local_ollama"},
        },
        "default_agent": "mistral",
        "total_agents": 6,
        "enabled_agents": 6,
        "available_agents": 2
    })
    mock.generate_mock_response = AsyncMock(return_value={
        "status": "success",
        "response": "[MOCK] Test response",
        "agent_name": "mock",
        "tokens": 0
    })
    return mock


@pytest.fixture
def mock_enhanced_chat_service(mock_agent_response):
    """Mock EnhancedChatService for testing."""
    mock = MagicMock()
    mock.process_message = AsyncMock(return_value={
        **mock_agent_response,
        "session_id": "test-session-123",
        "facts_extracted": 0
    })
    return mock


@pytest.fixture
def mock_memory_service():
    """Mock MemoryService for testing without real memory."""
    mock = MagicMock()
    mock.get_facts = MagicMock(return_value=[
        {"id": 1, "text": "User likes Python", "importance": 0.8, "tags": ["programming"]},
        {"id": 2, "text": "User is a QA Engineer", "importance": 0.9, "tags": ["occupation"]}
    ])
    mock.save_fact = MagicMock(return_value=1)
    mock.delete_fact = MagicMock(return_value=True)
    mock.get_chat_history = MagicMock(return_value=[])
    mock.get_stats = MagicMock(return_value={
        "total_facts": 10,
        "total_sessions": 5,
        "total_messages": 50
    })
    mock.search_facts = MagicMock(return_value=[
        {"id": 1, "text": "User likes Python", "importance": 0.8, "score": 0.95}
    ])
    return mock


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_session_id():
    """Provide consistent session ID for tests."""
    return "test-session-12345"


@pytest.fixture
def sample_chat_request(sample_session_id):
    """Sample chat request payload."""
    return {
        "message": "Hello, how are you today?",
        "session_id": sample_session_id,
        "agent": "mistral"
    }


@pytest.fixture
def sample_fact():
    """Sample fact for memory tests."""
    return {
        "text": "User prefers dark mode interfaces",
        "importance": 0.7,
        "tags": ["preference", "ui"]
    }


@pytest.fixture
def created_session(client):
    """Create a session and return its ID."""
    response = client.post("/api/v1/sessions", json={"title": "Test Session"})
    if response.status_code == 200:
        return response.json().get("session_id") or response.json().get("id")
    # Fallback for different API structures
    return "fallback-session-id"
