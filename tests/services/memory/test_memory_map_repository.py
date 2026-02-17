"""
Tests for MemoryMapRepository — persistence of MemoryMap graph to SQLite.

Uses synchronous in-memory SQLite for fast, isolated tests.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.memory_graph import MemoryEdgeModel, MemoryNodeModel
from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_map_repository import MemoryMapRepository
from app.services.memory.memory_node import MemoryNode


@pytest.fixture
def db():
    """Create a synchronous in-memory SQLite database with all tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def repo(db):
    """Create a MemoryMapRepository with the test DB session."""
    return MemoryMapRepository(db)


class TestMemoryMapRepository:

    def test_save_and_load_node(self, repo):
        """Save a node, load the map, verify the node is present with correct fields."""
        # Arrange
        node = MemoryNode(id="n1", content="User lives in Paris", node_type="fact", importance=0.8)

        # Act
        repo.save_node(node, session_id="sess-1")
        loaded_map = repo.load_map(session_id="sess-1")

        # Assert
        assert loaded_map.node_count == 1
        loaded_node = loaded_map.get_node("n1")
        assert loaded_node is not None
        assert loaded_node.content == "User lives in Paris"
        assert loaded_node.node_type == "fact"
        assert loaded_node.importance == 0.8

    def test_save_and_load_edge(self, repo):
        """Save two nodes and an edge, load the map, verify edge connects them."""
        # Arrange
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User speaks French", node_type="fact")
        edge = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.9)

        # Act
        repo.save_node(n1, session_id="sess-1")
        repo.save_node(n2, session_id="sess-1")
        repo.save_edge(edge)
        loaded_map = repo.load_map(session_id="sess-1")

        # Assert
        assert loaded_map.node_count == 2
        assert loaded_map.edge_count == 1
        assert loaded_map.get_node("n1") is not None
        assert loaded_map.get_node("n2") is not None
        loaded_edge = loaded_map.edges[0]
        assert loaded_edge.source_id == "n1"
        assert loaded_edge.target_id == "n2"
        assert loaded_edge.edge_type == "related_to"
        assert loaded_edge.weight == 0.9

    def test_load_empty_session(self, repo):
        """Loading a nonexistent session returns an empty MemoryMap, not None."""
        # Act
        loaded_map = repo.load_map(session_id="nonexistent-session")

        # Assert
        assert loaded_map is not None
        assert loaded_map.node_count == 0
        assert loaded_map.edge_count == 0

    def test_delete_node_cascades_edges(self, repo):
        """Deleting a node also deletes edges referencing it."""
        # Arrange
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User speaks French", node_type="fact")
        edge = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8)
        repo.save_node(n1, session_id="sess-1")
        repo.save_node(n2, session_id="sess-1")
        repo.save_edge(edge)

        # Act
        repo.delete_node("n1")
        loaded_map = repo.load_map(session_id="sess-1")

        # Assert — n1 and edge gone, n2 still present
        assert loaded_map.node_count == 1
        assert loaded_map.get_node("n1") is None
        assert loaded_map.get_node("n2") is not None
        assert loaded_map.edge_count == 0

    def test_delete_map_clears_all(self, repo):
        """Deleting a session's map removes all its nodes and edges, leaves other sessions intact."""
        # Arrange — sess-1: 3 nodes + 2 edges, sess-2: 1 node
        for i in range(1, 4):
            repo.save_node(
                MemoryNode(id=f"n{i}", content=f"Content {i}", node_type="fact"),
                session_id="sess-1",
            )
        repo.save_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to"))
        repo.save_edge(MemoryEdge(source_id="n2", target_id="n3", edge_type="related_to"))
        repo.save_node(
            MemoryNode(id="other-1", content="Other session node", node_type="fact"),
            session_id="sess-2",
        )

        # Act
        repo.delete_map("sess-1")

        # Assert — sess-1 gone, sess-2 intact
        sess1_map = repo.load_map("sess-1")
        assert sess1_map.node_count == 0
        assert sess1_map.edge_count == 0

        sess2_map = repo.load_map("sess-2")
        assert sess2_map.node_count == 1
        assert sess2_map.get_node("other-1") is not None

    def test_load_preserves_weights(self, repo):
        """Verify importance and weight values survive the save/load round-trip."""
        # Arrange
        node = MemoryNode(id="n1", content="Important node", node_type="fact", importance=0.9)
        edge_node = MemoryNode(id="n2", content="Connected node", node_type="fact")
        edge = MemoryEdge(source_id="n1", target_id="n2", edge_type="supports", weight=0.75)

        # Act
        repo.save_node(node, session_id="sess-1")
        repo.save_node(edge_node, session_id="sess-1")
        repo.save_edge(edge)
        loaded_map = repo.load_map(session_id="sess-1")

        # Assert
        assert loaded_map.get_node("n1").importance == 0.9
        assert loaded_map.edges[0].weight == 0.75
