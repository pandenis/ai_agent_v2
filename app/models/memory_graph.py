"""
SQLAlchemy models for persisting MemoryMap graph nodes and edges to SQLite.

Tables:
- memory_nodes: Graph nodes representing individual memory units
- memory_edges: Directed relationships between memory nodes
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_node import MemoryNode


class MemoryNodeModel(Base):
    """SQLAlchemy model for memory graph nodes."""

    __tablename__ = "memory_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False, default="fact")
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<MemoryNodeModel(node_id={self.node_id}, type={self.node_type}, importance={self.importance})>"

    def to_dataclass(self) -> MemoryNode:
        """Convert SQLAlchemy model to MemoryNode dataclass."""
        return MemoryNode(
            id=self.node_id,
            content=self.content,
            node_type=self.node_type,
            importance=self.importance,
            created_at=self.created_at,
            last_accessed=self.last_accessed,
            access_count=self.access_count,
        )


class MemoryEdgeModel(Base):
    """SQLAlchemy model for memory graph edges."""

    __tablename__ = "memory_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    edge_type: Mapped[str] = mapped_column(String(50), nullable=False, default="related_to")
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<MemoryEdgeModel('{self.source_node_id}' -> '{self.target_node_id}', type={self.edge_type}, weight={self.weight})>"

    def to_dataclass(self) -> MemoryEdge:
        """Convert SQLAlchemy model to MemoryEdge dataclass."""
        return MemoryEdge(
            source_id=self.source_node_id,
            target_id=self.target_node_id,
            edge_type=self.edge_type,
            weight=self.weight,
            created_at=self.created_at,
        )
