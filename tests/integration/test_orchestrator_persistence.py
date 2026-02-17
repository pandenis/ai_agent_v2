"""
Integration test: Orchestrator wiring to persistent MemoryMap.

Verifies that _load_memory_map creates a persistence-enabled MemoryMap
and that data written through it survives a reload.
"""

import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.services.memory.memory_map_repository import MemoryMapRepository
from app.services.memory.memory_node import MemoryNode
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.fixture
def db_session():
    """Create a synchronous in-memory SQLite database with all tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_orchestrator_uses_persistent_memory_map(db_session):
    """_load_memory_map wires a real MemoryMapRepository, and writes persist."""
    # Arrange — create orchestrator with no memory_map
    orchestrator = IntelligentOrchestrator(
        memory_service=MagicMock(),
        agent_factory=MagicMock(),
    )
    assert orchestrator.memory_map is None

    # Patch SyncSessionFactory to return our in-memory test session
    mock_factory = MagicMock(return_value=db_session)
    with patch(
        "app.services.orchestrator.orchestrator.SyncSessionFactory",
        mock_factory,
        create=True,
    ):
        # Patch the import inside _load_memory_map
        with patch.dict(
            "sys.modules",
        ):
            # We need to patch the SyncSessionFactory that's imported inside the method
            import app.core.database
            original_factory = app.core.database.SyncSessionFactory
            app.core.database.SyncSessionFactory = mock_factory
            try:
                # Act — trigger the load
                orchestrator._load_memory_map("sess-1")
            finally:
                app.core.database.SyncSessionFactory = original_factory

    # Assert — memory_map is set with repository enabled
    assert orchestrator.memory_map is not None
    assert orchestrator.memory_map._repository is not None
    assert orchestrator.memory_map._session_id == "sess-1"

    # Act — write through the memory_map
    node = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
    orchestrator.memory_map.add_node(node)

    # Assert — data persisted: re-load from same DB and verify
    repo = MemoryMapRepository(db_session)
    reloaded = repo.load_map("sess-1")
    assert reloaded.node_count == 1
    assert reloaded.get_node("n1").content == "User lives in Paris"
