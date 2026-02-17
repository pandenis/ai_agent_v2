"""
Repository for persisting MemoryMap graph data to SQLite.
"""
from sqlalchemy import delete, select, or_
from sqlalchemy.orm import Session

from app.models.memory_graph import MemoryEdgeModel, MemoryNodeModel
from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_node import MemoryNode


class MemoryMapRepository:
    """
    Repository for persisting MemoryMap graph data to SQLite.

    Handles saving and loading of MemoryNode and MemoryEdge objects,
    converting between domain dataclasses and SQLAlchemy models.

    Usage:
        >>> repo = MemoryMapRepository(db_session)
        >>> repo.save_node(node, session_id="sess-1")
        >>> memory_map = repo.load_map(session_id="sess-1")
    """

    def __init__(self, session: Session):
        self.session = session

    def save_node(self, node: MemoryNode, session_id: str) -> None:
        """Save a MemoryNode, inserting or updating if node_id already exists."""
        existing = self.session.execute(
            select(MemoryNodeModel).where(MemoryNodeModel.node_id == node.id)
        ).scalar_one_or_none()

        if existing:
            existing.content = node.content
            existing.node_type = node.node_type
            existing.importance = node.importance
            existing.access_count = node.access_count
            existing.last_accessed = node.last_accessed
            existing.session_id = session_id
        else:
            model = MemoryNodeModel(
                node_id=node.id,
                content=node.content,
                node_type=node.node_type,
                importance=node.importance,
                access_count=node.access_count,
                created_at=node.created_at,
                last_accessed=node.last_accessed,
                session_id=session_id,
            )
            self.session.add(model)

        self.session.commit()

    def save_edge(self, edge: MemoryEdge) -> None:
        """Save a MemoryEdge to the database."""
        model = MemoryEdgeModel(
            source_node_id=edge.source_id,
            target_node_id=edge.target_id,
            edge_type=edge.edge_type,
            weight=edge.weight,
            created_at=edge.created_at,
        )
        self.session.add(model)
        self.session.commit()

    def load_map(self, session_id: str) -> MemoryMap:
        """Load all nodes and edges for a session into a MemoryMap."""
        memory_map = MemoryMap()

        # Load nodes
        node_models = self.session.execute(
            select(MemoryNodeModel).where(MemoryNodeModel.session_id == session_id)
        ).scalars().all()

        node_ids = set()
        for model in node_models:
            memory_map.add_node(model.to_dataclass())
            node_ids.add(model.node_id)

        if not node_ids:
            return memory_map

        # Load edges where both endpoints belong to this session
        edge_models = self.session.execute(
            select(MemoryEdgeModel).where(
                MemoryEdgeModel.source_node_id.in_(node_ids),
                MemoryEdgeModel.target_node_id.in_(node_ids),
            )
        ).scalars().all()

        for model in edge_models:
            memory_map.add_edge(model.to_dataclass())

        return memory_map

    def delete_node(self, node_id: str) -> None:
        """Delete a node and any edges referencing it."""
        self.session.execute(
            delete(MemoryEdgeModel).where(
                or_(
                    MemoryEdgeModel.source_node_id == node_id,
                    MemoryEdgeModel.target_node_id == node_id,
                )
            )
        )
        self.session.execute(
            delete(MemoryNodeModel).where(MemoryNodeModel.node_id == node_id)
        )
        self.session.commit()

    def delete_map(self, session_id: str) -> None:
        """Delete all nodes and edges for a session."""
        # Get node IDs for this session
        node_ids = [
            row[0] for row in self.session.execute(
                select(MemoryNodeModel.node_id).where(
                    MemoryNodeModel.session_id == session_id
                )
            ).all()
        ]

        if node_ids:
            self.session.execute(
                delete(MemoryEdgeModel).where(
                    or_(
                        MemoryEdgeModel.source_node_id.in_(node_ids),
                        MemoryEdgeModel.target_node_id.in_(node_ids),
                    )
                )
            )

        self.session.execute(
            delete(MemoryNodeModel).where(MemoryNodeModel.session_id == session_id)
        )
        self.session.commit()
