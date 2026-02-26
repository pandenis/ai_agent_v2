"""Integration test: messages are persisted after /orchestrate call."""
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.deps import get_orchestrator, get_db
from app.services.orchestrator.orchestrator import IntelligentOrchestrator
from app.core.database import Base


@pytest.mark.asyncio
async def test_messages_saved_after_orchestrate():
    """POST /orchestrate saves user+assistant messages; GET /messages returns them."""

    # --- In-memory test database ---
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    # --- Mock orchestrator (avoids real AI / DB calls inside orchestrator) ---
    mock_memory = AsyncMock()
    mock_memory.search_facts = AsyncMock(return_value=[])
    mock_memory.get_conversation_history = AsyncMock(return_value=[])

    mock_agent = AsyncMock()
    mock_agent.name = "test-agent"
    mock_agent.generate = AsyncMock(return_value={"response": "Hello Denis!"})

    mock_factory = Mock()
    mock_factory.create_agent = Mock(return_value=mock_agent)

    orchestrator = IntelligentOrchestrator(
        memory_service=mock_memory,
        agent_factory=mock_factory,
    )
    # Prevent _load_memory_map from hitting the real DB
    mock_memory_map = MagicMock()
    mock_memory_map.build_context_for_query = MagicMock(return_value="")
    orchestrator.memory_map = mock_memory_map

    # --- Dependency overrides ---
    async def override_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_db] = override_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Act: send query
            post_resp = await client.post(
                "/api/v1/orchestrate",
                json={"query": "My name is Denis", "session_id": "save-test-001"},
            )
            assert post_resp.status_code == 200, post_resp.text

            # Assert: messages persisted
            get_resp = await client.get("/api/v1/sessions/save-test-001/messages")
            assert get_resp.status_code == 200, get_resp.text
            data = get_resp.json()
            assert data["total"] >= 1, f"Expected at least 1 message, got: {data}"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
