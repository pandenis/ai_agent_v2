"""
Integration tests for Memory API endpoints.

Tests:
- GET /memory/facts (list with filters)
- GET /memory/facts/{fact_id} (get one)
- DELETE /memory/facts/{fact_id}
- GET /memory/stats
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


# ============================================================================
# HELPER: Create client with mocked memory service
# ============================================================================

@pytest.fixture
async def client_with_mock_memory(test_engine):
    """Client with mocked MemoryService for memory endpoint tests."""
    from app.main import app
    from app.core.database import get_db
    from app.api.deps import get_memory_service
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    
    # Create session factory for test engine
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Override get_db
    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
    
    # Create mock memory service
    mock_service = MagicMock()
    mock_service.get_facts = AsyncMock(return_value=[])
    mock_service.get_fact_by_id = AsyncMock(return_value=None)
    mock_service.delete_fact = AsyncMock(return_value=False)
    mock_service.get_facts_stats = AsyncMock(return_value={
        "total_facts": 0,
        "facts_by_type": {},
        "avg_importance": 0.0
    })
    
    # Override memory service dependency
    async def override_get_memory_service():
        return mock_service
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_memory_service] = override_get_memory_service
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        # Attach mock for test customization
        ac.mock_memory_service = mock_service
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# TESTS
# ============================================================================

class TestGetFacts:
    """Tests for GET /memory/facts endpoint."""

    @pytest.mark.asyncio
    async def test_get_facts_success(self, client_with_mock_memory):
        """Test: GET /memory/facts returns facts list."""
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data
        assert "total" in data
        assert "has_more" in data

    @pytest.mark.asyncio
    async def test_get_facts_with_min_importance(self, client_with_mock_memory):
        """Test: GET /memory/facts filters by min_importance."""
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts?min_importance=0.8")
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_facts_with_fact_type(self, client_with_mock_memory):
        """Test: GET /memory/facts filters by fact_type."""
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts?fact_type=preference")
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_facts_with_tags(self, client_with_mock_memory):
        """Test: GET /memory/facts filters by tags."""
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts?tags=python,programming")
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_facts_with_pagination(self, client_with_mock_memory):
        """Test: GET /memory/facts supports pagination."""
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts?limit=10&offset=5")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5


class TestGetFactById:
    """Tests for GET /memory/facts/{fact_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_fact_by_id_success(self, client_with_mock_memory):
        """Test: GET /memory/facts/{id} returns fact."""
        # Arrange - configure mock to return a fact
        mock_fact = MagicMock()
        mock_fact.fact_id = "fact-123"
        mock_fact.text = "User likes Python"
        mock_fact.importance = 0.8
        mock_fact.confidence = 0.9
        mock_fact.tags = ["programming"]
        mock_fact.fact_type = "preference"
        mock_fact.source = "conversation"
        mock_fact.created = "2025-01-01T00:00:00"
        mock_fact.updated = "2025-01-01T00:00:00"
        mock_fact.last_accessed = "2025-01-01T00:00:00"
        mock_fact.usage_count = 5
        mock_fact.needs_update = False
        
        client_with_mock_memory.mock_memory_service.get_fact_by_id = AsyncMock(return_value=mock_fact)
        
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts/fact-123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["fact_id"] == "fact-123"
        assert data["text"] == "User likes Python"

    @pytest.mark.asyncio
    async def test_get_fact_by_id_not_found(self, client_with_mock_memory):
        """Test: GET /memory/facts/{id} returns 404 when not found."""
        # Arrange - mock returns None (default)
        client_with_mock_memory.mock_memory_service.get_fact_by_id = AsyncMock(return_value=None)
        
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/facts/nonexistent-fact")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDeleteFact:
    """Tests for DELETE /memory/facts/{fact_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_fact_success(self, client_with_mock_memory):
        """Test: DELETE /memory/facts/{id} deletes fact."""
        # Arrange - mock fact exists
        from app.models.memory_v2 import FactModel
        from app.api.deps import get_write_gate
        from app.main import app
        from app.services.memory_write_gate import WriteResult

        mock_fact = MagicMock(spec=FactModel)
        mock_fact.thread_id = "test-thread"
        client_with_mock_memory.mock_memory_service.get_fact_by_id = AsyncMock(return_value=mock_fact)
        client_with_mock_memory.mock_memory_service.delete_fact = AsyncMock(return_value=True)

        # Mock WriteGate
        mock_write_gate = MagicMock()
        mock_write_gate.execute = AsyncMock(return_value=WriteResult(
            success=True,
            facts_written=1,
            operation="delete",
            thread_id="test-thread",
            source="api",
            fact_ids=[]
        ))
        app.dependency_overrides[get_write_gate] = lambda: mock_write_gate

        # Act
        response = await client_with_mock_memory.delete("/api/v1/memory/facts/fact-123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["fact_id"] == "fact-123"

    @pytest.mark.asyncio
    async def test_delete_fact_not_found(self, client_with_mock_memory):
        """Test: DELETE /memory/facts/{id} returns 404 when not found."""
        # Arrange
        client_with_mock_memory.mock_memory_service.delete_fact = AsyncMock(return_value=False)
        
        # Act
        response = await client_with_mock_memory.delete("/api/v1/memory/facts/nonexistent-fact")
        
        # Assert
        assert response.status_code == 404


class TestMemoryStats:
    """Tests for GET /memory/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_memory_stats_success(self, client_with_mock_memory):
        """Test: GET /memory/stats returns statistics."""
        # Arrange
        client_with_mock_memory.mock_memory_service.get_facts_stats = AsyncMock(return_value={
            "total_facts": 42,
            "facts_by_type": {"preference": 10, "personal": 15, "professional": 17},
            "avg_importance": 0.75
        })
        
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_facts"] == 42
        assert "facts_by_type" in data
        assert data["avg_importance"] == 0.75

    @pytest.mark.asyncio
    async def test_get_memory_stats_empty(self, client_with_mock_memory):
        """Test: GET /memory/stats handles empty memory."""
        # Arrange - default mock returns empty stats
        
        # Act
        response = await client_with_mock_memory.get("/api/v1/memory/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_facts"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
