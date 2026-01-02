"""
Integration test fixtures and configuration.

This module provides:
- Async database for testing (matching app's async routes)
- Mocked services (AgentService, MemoryService, Ollama)
- Test client with dependency overrides
- Sample data fixtures
"""

import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Detect CI environment
IN_CI = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"


# ============================================================================
# DATABASE FIXTURES (Async)
# ============================================================================

@pytest.fixture(scope="function")
async def test_engine():
    """Create async SQLite engine for testing."""
    from app.core.database import Base
    
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine):
    """Create async database session for each test."""
    async_session = async_sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_engine):
    """Create async test client with DB override."""
    from app.main import app
    from app.core.database import get_db
    
    # Create session factory for test engine
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Override get_db dependency
    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use httpx AsyncClient with ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
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
def mock_memory_service():
    """Mock MemoryService for testing without real memory."""
    mock = MagicMock()
    mock.get_facts = AsyncMock(return_value=[])
    mock.save_fact = AsyncMock(return_value=1)
    mock.delete_fact = AsyncMock(return_value=True)
    mock.get_chat_history = AsyncMock(return_value=[])
    mock.get_facts_stats = AsyncMock(return_value={
        "total_facts": 0,
        "facts_by_type": {},
        "avg_importance": 0.0
    })
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
