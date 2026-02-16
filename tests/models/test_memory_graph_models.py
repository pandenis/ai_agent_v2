"""
Tests for MemoryNodeModel and MemoryEdgeModel SQLAlchemy models.

Uses synchronous in-memory SQLite for fast, isolated model-level tests.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.memory_graph import MemoryEdgeModel, MemoryNodeModel


@pytest.fixture
def db():
    """Create a synchronous in-memory SQLite database with all tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


class TestMemoryGraphModels:

    def test_memory_node_model_creation(self, db):
        """Create a MemoryNodeModel, persist it, and verify all fields."""
        # Arrange
        node = MemoryNodeModel(
            node_id="node-1",
            content="User lives in Paris",
            node_type="fact",
            importance=0.8,
            session_id="session-abc",
        )

        # Act
        db.add(node)
        db.commit()
        result = db.execute(
            select(MemoryNodeModel).where(MemoryNodeModel.node_id == "node-1")
        ).scalar_one()

        # Assert
        assert result.node_id == "node-1"
        assert result.content == "User lives in Paris"
        assert result.node_type == "fact"
        assert result.importance == 0.8
        assert result.session_id == "session-abc"
        assert result.access_count == 0
        assert result.created_at is not None
        assert result.last_accessed is not None

    def test_memory_edge_model_creation(self, db):
        """Create two nodes and an edge between them, verify edge fields."""
        # Arrange
        node1 = MemoryNodeModel(
            node_id="node-1",
            content="User lives in Paris",
            node_type="fact",
            importance=0.8,
            session_id="session-abc",
        )
        node2 = MemoryNodeModel(
            node_id="node-2",
            content="User speaks French",
            node_type="fact",
            importance=0.7,
            session_id="session-abc",
        )
        edge = MemoryEdgeModel(
            source_node_id="node-1",
            target_node_id="node-2",
            edge_type="related_to",
            weight=0.9,
        )

        # Act
        db.add_all([node1, node2, edge])
        db.commit()
        result = db.execute(
            select(MemoryEdgeModel).where(
                MemoryEdgeModel.source_node_id == "node-1"
            )
        ).scalar_one()

        # Assert
        assert result.source_node_id == "node-1"
        assert result.target_node_id == "node-2"
        assert result.edge_type == "related_to"
        assert result.weight == 0.9
        assert result.created_at is not None

    def test_memory_node_model_constraints(self, db):
        """Verify unique constraint on node_id and non-null requirements."""
        # Arrange — first node succeeds
        node1 = MemoryNodeModel(
            node_id="dup-1",
            content="First node",
            node_type="fact",
            session_id="session-abc",
        )
        db.add(node1)
        db.commit()

        # Act / Assert — duplicate node_id raises IntegrityError
        node2 = MemoryNodeModel(
            node_id="dup-1",
            content="Duplicate node",
            node_type="fact",
            session_id="session-abc",
        )
        db.add(node2)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        # Act / Assert — null node_id raises IntegrityError
        node3 = MemoryNodeModel(
            node_id=None,
            content="Missing ID",
            node_type="fact",
            session_id="session-abc",
        )
        db.add(node3)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_memory_edge_model_foreign_keys(self, db):
        """Verify edge model stores node_id strings correctly and is queryable."""
        # Arrange
        edge = MemoryEdgeModel(
            source_node_id="src-node",
            target_node_id="tgt-node",
            edge_type="caused_by",
            weight=0.75,
        )

        # Act
        db.add(edge)
        db.commit()

        # Query by source
        by_source = db.execute(
            select(MemoryEdgeModel).where(
                MemoryEdgeModel.source_node_id == "src-node"
            )
        ).scalar_one()
        assert by_source.target_node_id == "tgt-node"
        assert by_source.edge_type == "caused_by"
        assert by_source.weight == 0.75

        # Query by target
        by_target = db.execute(
            select(MemoryEdgeModel).where(
                MemoryEdgeModel.target_node_id == "tgt-node"
            )
        ).scalar_one()
        assert by_target.source_node_id == "src-node"
