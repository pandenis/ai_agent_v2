"""
Integration test: MemoryMap persistence across instances.

Proves that graph data survives a "restart" — create a MemoryMap,
add data, create a second MemoryMap from the same repository,
and verify the data is present.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_map_repository import MemoryMapRepository
from app.services.memory.memory_node import MemoryNode


@pytest.fixture
def db_session():
    """Create a synchronous in-memory SQLite database with all tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_memory_map_persists_across_instances(db_session):
    """Graph data written via one MemoryMap instance is visible from a fresh instance."""
    # Arrange — first instance: write data
    repo = MemoryMapRepository(db_session)
    map1 = MemoryMap.from_repository(repo, session_id="sess-1")

    n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact", importance=0.8)
    n2 = MemoryNode(id="n2", content="User speaks French", node_type="fact", importance=0.7)
    edge = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.9)

    map1.add_node(n1)
    map1.add_node(n2)
    map1.add_edge(edge)

    # Act — second instance: simulate restart by loading from same repo
    map2 = MemoryMap.from_repository(repo, session_id="sess-1")

    # Assert — data survived
    assert map2.node_count == 2
    assert map2.edge_count == 1
    assert map2.get_node("n1").content == "User lives in Paris"
    assert map2.get_node("n2").content == "User speaks French"
    assert map2.edges[0].source_id == "n1"
    assert map2.edges[0].target_id == "n2"
    assert map2.edges[0].edge_type == "related_to"
    assert map2.edges[0].weight == 0.9
