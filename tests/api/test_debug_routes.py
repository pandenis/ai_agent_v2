"""Tests for GET /api/v1/debug/memory/{session_id}."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_orchestrator
from app.main import app
from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_node import MemoryNode


def _make_mock_orchestrator(memory_map=None):
    """Return a lightweight object that quacks like IntelligentOrchestrator."""

    class _Stub:
        pass

    stub = _Stub()
    stub.memory_map = memory_map
    return stub


def _override_orchestrator(memory_map=None):
    """Register a dependency override that returns a stub orchestrator."""

    async def _dep():
        return _make_mock_orchestrator(memory_map)

    app.dependency_overrides[get_orchestrator] = _dep


def _build_populated_map() -> MemoryMap:
    """Build a MemoryMap with 2 nodes and 1 edge for testing."""
    mm = MemoryMap()
    mm.add_node(MemoryNode(id="n1", content="User lives in Seoul", node_type="fact", importance=0.9))
    mm.add_node(MemoryNode(id="n2", content="User speaks Korean", node_type="fact", importance=0.8))
    mm.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
    return mm


class TestDebugMemoryEndpoint:
    """Tests for the debug memory inspection endpoint."""

    @pytest.fixture(autouse=True)
    def _cleanup_overrides(self):
        """Ensure dependency overrides are cleared after each test."""
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_debug_memory_endpoint_returns_200(self):
        """GET /debug/memory/{session_id} returns 200 with expected top-level keys."""
        # Arrange
        _override_orchestrator(memory_map=None)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/test-session")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "graph_stats" in data
        assert "nodes" in data
        assert "edges" in data

    @pytest.mark.asyncio
    async def test_debug_memory_endpoint_empty_session(self):
        """A session with no MemoryMap returns 200 with empty graph."""
        # Arrange
        _override_orchestrator(memory_map=None)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/nonexistent-session")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["graph_stats"]["node_count"] == 0
        assert data["nodes"] == []
        assert data["edges"] == []

    @pytest.mark.asyncio
    async def test_debug_memory_endpoint_session_id_in_response(self):
        """The response echoes back the requested session_id."""
        # Arrange
        _override_orchestrator(memory_map=None)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/my-test-session")

        # Assert
        data = response.json()
        assert data["session_id"] == "my-test-session"

    @pytest.mark.asyncio
    async def test_debug_memory_endpoint_with_populated_map(self):
        """A populated MemoryMap is correctly serialized in the response."""
        # Arrange
        mm = _build_populated_map()
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/populated-session")

        # Assert
        data = response.json()
        assert data["graph_stats"]["node_count"] == 2
        assert data["graph_stats"]["edge_count"] == 1
        assert len(data["nodes"]) == 2
        assert any(n["content"] == "User lives in Seoul" for n in data["nodes"])
        assert len(data["edges"]) == 1
        assert data["edges"][0]["edge_type"] == "related_to"

    @pytest.mark.asyncio
    async def test_debug_memory_node_includes_weight(self):
        """Each node in the response includes a weight float between 0.0 and 1.0."""
        # Arrange
        mm = _build_populated_map()
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/weight-session")

        # Assert
        data = response.json()
        for node in data["nodes"]:
            assert "weight" in node
            assert isinstance(node["weight"], float)
            assert 0.0 <= node["weight"] <= 1.0

    @pytest.mark.asyncio
    async def test_debug_endpoint_includes_enriched_stats(self):
        """Enriched stats include avg_importance and avg_weight."""
        # Arrange
        mm = MemoryMap()
        mm.add_node(MemoryNode(id="n1", content="Fact one", node_type="fact", importance=0.9))
        mm.add_node(MemoryNode(id="n2", content="Fact two", node_type="fact", importance=0.6))
        mm.add_node(MemoryNode(id="n3", content="Fact three", node_type="fact", importance=0.3))
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/enriched-session")

        # Assert
        data = response.json()
        assert data["graph_stats"]["node_count"] == 3
        assert abs(data["graph_stats"]["avg_importance"] - 0.6) < 0.05
        assert isinstance(data["graph_stats"]["avg_weight"], float)
        assert 0.0 <= data["graph_stats"]["avg_weight"] <= 1.0

    @pytest.mark.asyncio
    async def test_debug_endpoint_includes_retrieval_history(self):
        """Recent retrieval logs are included in the response."""
        # Arrange
        mm = MemoryMap()
        mm.add_node(MemoryNode(id="n1", content="User lives in Seoul", node_type="fact", importance=0.9))
        mm.add_node(MemoryNode(id="n2", content="User speaks Korean", node_type="fact", importance=0.8))
        mm.build_context_for_query("test query 1", 500)
        mm.build_context_for_query("test query 2", 500)
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/retrieval-session")

        # Assert
        data = response.json()
        assert len(data["recent_retrievals"]) == 2
        assert data["recent_retrievals"][0]["query"] == "test query 1"
        assert data["recent_retrievals"][1]["query"] == "test query 2"
        for entry in data["recent_retrievals"]:
            assert "nodes_scored" in entry
            assert "nodes_returned" in entry
            assert "elapsed_ms" in entry
            assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_debug_endpoint_includes_write_history(self):
        """Recent write logs are included in the response."""
        # Arrange
        mm = MemoryMap()
        mm.add_node(MemoryNode(id="n1", content="Write test one", node_type="fact"))
        mm.add_node(MemoryNode(id="n2", content="Write test two", node_type="fact"))
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/write-session")

        # Assert
        data = response.json()
        assert len(data["recent_writes"]) >= 2
        assert data["recent_writes"][0]["operation"] == "add_node"
        for entry in data["recent_writes"]:
            assert "operation" in entry
            assert "node_id" in entry
            assert "dedup_detected" in entry
            assert "success" in entry
            assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_debug_endpoint_limits_history_to_5(self):
        """Retrieval history is capped at 5 entries."""
        # Arrange
        mm = MemoryMap()
        mm.add_node(MemoryNode(id="n1", content="Limit test node", node_type="fact"))
        for i in range(8):
            mm.build_context_for_query(f"query {i}", 500)
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/limit-session")

        # Assert
        data = response.json()
        assert len(data["recent_retrievals"]) <= 5

    @pytest.mark.asyncio
    async def test_debug_endpoint_empty_map_has_zero_averages(self):
        """No MemoryMap returns zero averages and empty history lists."""
        # Arrange
        _override_orchestrator(memory_map=None)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/empty-session")

        # Assert
        data = response.json()
        assert data["graph_stats"]["avg_importance"] == 0.0
        assert data["graph_stats"]["avg_weight"] == 0.0
        assert data["recent_retrievals"] == []
        assert data["recent_writes"] == []

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_200(self):
        """GET /debug/memory/metrics returns 200 with expected keys."""
        # Arrange
        _override_orchestrator(memory_map=None)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/metrics")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_retrievals" in data
        assert "total_writes" in data
        assert "avg_retrieval_ms" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint_empty_returns_zeros(self):
        """No MemoryMap returns zeroed metrics."""
        # Arrange
        _override_orchestrator(memory_map=None)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/metrics")

        # Assert
        data = response.json()
        assert data["total_retrievals"] == 0
        assert data["total_writes"] == 0
        assert data["avg_retrieval_ms"] == 0.0

    @pytest.mark.asyncio
    async def test_metrics_endpoint_reflects_operations(self):
        """Metrics reflect add_node, add_edge, and retrieval operations."""
        # Arrange
        mm = _build_populated_map()  # 2 add_node + 1 add_edge = 3 writes
        mm.build_context_for_query("Seoul", 500)
        _override_orchestrator(memory_map=mm)

        # Act
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/debug/memory/metrics")

        # Assert
        data = response.json()
        assert data["total_retrievals"] >= 1
        assert data["total_writes"] >= 3
        assert data["total_write_ops_by_type"]["add_node"] >= 2
