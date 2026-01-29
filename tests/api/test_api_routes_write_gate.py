"""
Tests for API routes using MemoryWriteGate

Epic 2: Memory Write Centralization
Task 2.4: Refactor API routes to delegate writes to MemoryWriteGate

Why this exists:
- API routes should use MemoryWriteGate for all memory writes
- Dependency injection for write_gate enables centralized control
- DELETE operations should go through gate for audit/validation
- Enhanced chat should receive write_gate for fact extraction
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


class TestGetWriteGateDependency:
    """Test that get_write_gate dependency exists and works."""

    def test_get_write_gate_function_exists(self):
        """Test: get_write_gate function is importable from deps."""
        from app.api.deps import get_write_gate

        assert callable(get_write_gate)

    @pytest.mark.asyncio
    async def test_get_write_gate_returns_write_gate(self):
        """Test: get_write_gate returns a MemoryWriteGate instance."""
        from app.api.deps import get_write_gate
        from app.services.memory_write_gate import MemoryWriteGate
        from app.services.memory_service import MemoryService
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from app.core.database import Base

        # Setup test database
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Get memory service first
            memory_service = MemoryService(session)

            # Get write gate
            write_gate = get_write_gate(memory_service)

            assert isinstance(write_gate, MemoryWriteGate)
            assert write_gate.memory_service == memory_service

        await engine.dispose()

class TestEnhancedChatEndpointWithGate:
    """Test /chat/enhanced endpoint receives write_gate."""

    @pytest.mark.asyncio
    async def test_enhanced_chat_receives_write_gate(self):
        """Test: Enhanced chat endpoint injects write_gate into service."""
        from app.main import app
        from app.api.deps import get_write_gate, get_memory_service, get_agent_service
        from app.services.memory_write_gate import MemoryWriteGate
        from app.services.enhanced_chat_service import EnhancedChatService
        from app.services.document_service import DocumentService
        from app.services.web_search_service import WebSearchService

        # Track if EnhancedChatService received write_gate
        received_write_gate = [None]  # Use list to capture in closure

        # Create mocks
        mock_gate = MagicMock(spec=MemoryWriteGate)
        mock_memory = MagicMock()
        mock_memory.get_conversation_history = AsyncMock(return_value=[])
        mock_memory.search_facts = AsyncMock(return_value=[])
        mock_memory.add_message = AsyncMock()

        mock_agent = MagicMock()
        mock_agent.chat = AsyncMock(return_value="Hello!")
        mock_agent.get_available_agents = MagicMock(return_value=["test-agent"])

        mock_doc_service = MagicMock(spec=DocumentService)
        mock_doc_service.search = AsyncMock(return_value=[])

        mock_web_service = MagicMock(spec=WebSearchService)
        mock_web_service.search = AsyncMock(return_value=[])

        # Override dependencies
        app.dependency_overrides[get_write_gate] = lambda: mock_gate
        app.dependency_overrides[get_memory_service] = lambda: mock_memory
        app.dependency_overrides[get_agent_service] = lambda: mock_agent

        try:
            # Patch EnhancedChatService to capture write_gate and return mock response
            with patch('app.api.routes.EnhancedChatService') as MockChatService:
                mock_instance = MagicMock()
                mock_instance.process_message = AsyncMock(return_value={
                    "response": "Hello!",
                    "agent_used": "test",
                    "sources": [],
                    "facts_extracted": 0
                })
                MockChatService.return_value = mock_instance

                # Also patch DocumentService and WebSearchService to avoid ChromaDB
                with patch('app.api.routes.DocumentService', return_value=mock_doc_service):
                    with patch('app.api.routes.WebSearchService', return_value=mock_web_service):
                        async with AsyncClient(
                            transport=ASGITransport(app=app),
                            base_url="http://test"
                        ) as client:
                            response = await client.post(
                                "/api/v1/chat/enhanced",
                                json={
                                    "session_id": "test-session-12345678",
                                    "message": "Hello"
                                }
                            )

                            # Verify EnhancedChatService was called with write_gate
                            MockChatService.assert_called_once()
                            call_kwargs = MockChatService.call_args[1]
                            assert 'write_gate' in call_kwargs
                            assert call_kwargs['write_gate'] == mock_gate
        finally:
            app.dependency_overrides.clear()


class TestDeleteFactWithThreadId:

    @pytest.mark.asyncio
    async def test_delete_nonexistent_fact_returns_404(self):
        """Test: DELETE returns 404 for non-existent fact."""
        from app.main import app
        from app.api.deps import get_write_gate, get_memory_service
        from app.services.memory_write_gate import MemoryWriteGate

        mock_gate = MagicMock(spec=MemoryWriteGate)
        mock_memory = MagicMock()
        mock_memory.get_fact_by_id = AsyncMock(return_value=None)  # Fact not found

        app.dependency_overrides[get_write_gate] = lambda: mock_gate
        app.dependency_overrides[get_memory_service] = lambda: mock_memory

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.delete("/api/v1/memory/facts/nonexistent")

                assert response.status_code == 404
                # Should NOT call write_gate for non-existent fact
                mock_gate.execute.assert_not_called()
        finally:
            app.dependency_overrides.clear()