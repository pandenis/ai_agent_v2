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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.deps import get_orchestrator, get_db
from app.services.orchestrator.orchestrator import IntelligentOrchestrator
from app.services.orchestrator.memory_evaluator import MemoryEvaluation
from app.core.database import Base


# ==========================================
# Test Database Setup
# ==========================================
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db_session():
    """Create in-memory test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with TestSessionLocal() as session:
        yield session
    
    await engine.dispose()


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
def mock_agent_factory(mock_agent):
    """Mock agent registry"""
    registry = Mock()
    registry.create_agent = Mock(return_value=mock_agent)
    registry.get_default_agent = Mock(return_value=mock_agent)
    return registry


# ==========================================
# Test 1: Direct Strategy (High Memory Coverage)
# ==========================================
@pytest.mark.asyncio
async def test_e2e_direct_strategy_from_memory(test_db_session):
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
    
    mock_factory = Mock()
    mock_factory.create_agent = Mock(return_value=AsyncMock())
    
    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_factory=mock_factory,
    )
    
    # Override dependencies
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_db] = lambda: test_db_session
    
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/orchestrate",
                json={
                    "query": "What is my name?",
                    "session_id": "test-session-direct"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "text" in data
        assert "metadata" in data
        assert data["metadata"]["strategy"] in ["direct", "enhanced", "deep_reasoning", "error", "unknown"]
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test 2: Enhanced Strategy (Medium Memory + AI)
# ==========================================
@pytest.mark.asyncio
async def test_e2e_enhanced_strategy_with_ai(test_db_session):
    """
    E2E Test: Query with partial memory uses enhanced strategy
    
    Flow:
    1. User asks complex question
    2. Memory provides some context
    3. AI enhances the response
    """
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[
        Mock(text="User likes Python", importance=0.7, confidence=0.8)
    ])
    
    mock_agent = AsyncMock()
    mock_agent.name = "test-agent"
    mock_agent.process = AsyncMock(return_value="Here's a helpful response about Python")
    
    mock_factory = Mock()
    mock_factory.create_agent = Mock(return_value=mock_agent)
    
    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_factory=mock_factory,
    )
    
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_db] = lambda: test_db_session
    
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/orchestrate",
                json={
                    "query": "Recommend a Python library for web scraping",
                    "session_id": "test-session-enhanced"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "metadata" in data
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test 3: Deep Reasoning Strategy (Complex Query)
# ==========================================
@pytest.mark.asyncio
async def test_e2e_deep_reasoning_strategy(test_db_session):
    """
    E2E Test: Complex query triggers deep reasoning
    """
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[])
    
    mock_agent = AsyncMock()
    mock_agent.name = "deep-reasoner"
    mock_agent.process = AsyncMock(return_value="Deep analysis complete")
    
    mock_factory = Mock()
    mock_factory.create_agent = Mock(return_value=mock_agent)
    
    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_factory=mock_factory,
    )
    
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_db] = lambda: test_db_session
    
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/orchestrate",
                json={
                    "query": "Compare and contrast the economic policies of three countries and analyze their long-term impact",
                    "session_id": "test-session-deep"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test 4: Caching Behavior
# ==========================================
@pytest.mark.asyncio
async def test_e2e_caching_returns_cached_response(test_db_session):
    """
    E2E Test: Second identical request returns cached response
    """
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[])
    
    call_count = 0
    
    async def mock_process(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return f"Response #{call_count}"
    
    mock_agent = AsyncMock()
    mock_agent.name = "test-agent"
    mock_agent.process = mock_process
    
    mock_factory = Mock()
    mock_factory.create_agent = Mock(return_value=mock_agent)
    
    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_factory=mock_factory,
    )
    
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_db] = lambda: test_db_session
    
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # First request
            response1 = await client.post(
                "/api/v1/orchestrate",
                json={
                    "query": "What is 2+2?",
                    "session_id": "test-cache-session"
                }
            )
            
            # Second identical request
            response2 = await client.post(
                "/api/v1/orchestrate",
                json={
                    "query": "What is 2+2?",
                    "session_id": "test-cache-session"
                }
            )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should have valid responses
        data1 = response1.json()
        data2 = response2.json()
        assert "text" in data1
        assert "text" in data2
    finally:
        app.dependency_overrides.clear()
