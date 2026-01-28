"""
Enhanced memory models for Memorisator
Version: 2.0
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


@dataclass
class Fact:
    """
    Enhanced fact model for Memorisator

    Represents a structured piece of information extracted from conversations
    with metadata for importance, confidence, and lifecycle management.
    """

    # Core fields
    fact_id: str
    text: str

    # Thread isolation (Epic 1)
    thread_id: Optional[str] = None

    # TTL & Lifecycle (Epic 3 - Task 3.1)
    ttl_days: Optional[int] = None  # Time-to-live in days (None = never expires)
    expires_at: Optional[datetime] = None  # Expiration timestamp

    # Metadata (renamed from metadata to avoid SQLAlchemy conflict)

    # Scoring
    importance: float = 0.5  # 0.0-1.0: How important is this fact?
    confidence: float = 0.8  # 0.0-1.0: How confident are we in this fact?
    tags: List[str] = field(default_factory=list)

    # Timestamps
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None

    # Type and updates
    fact_type: str = "static"  # static, weather, event, preference, knowledge
    needs_update: bool = False
    update_frequency: Optional[str] = None  # daily, weekly, monthly, None

    # Sources and relations
    source: str = "conversation"  # conversation, web_search, document, manual
    source_session_id: Optional[str] = None
    related_fact_ids: List[str] = field(default_factory=list)
    context_maps: List[str] = field(default_factory=list)

    # Metadata (renamed from metadata to avoid SQLAlchemy conflict)
    meta_data: Dict[str, Any] = field(default_factory=dict)
    usage_count: int = 0


class FactModel(Base):
    """
    SQLAlchemy model for facts table
    """
    __tablename__ = "facts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Thread isolation (Epic 1)
    thread_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Thread/session ID for isolation"
    )

    # TTL & Lifecycle (Epic 3 - Task 3.1)
    ttl_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Time-to-live in days (NULL = never expires)"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="Expiration timestamp for cleanup queries"
    )

    # Metadata (renamed to avoid SQLAlchemy conflict)

    # Core fields
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Scoring
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Type and updates
    fact_type: Mapped[str] = mapped_column(String(50), default="static")
    needs_update: Mapped[bool] = mapped_column(Boolean, default=False)
    update_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Sources and relations
    source: Mapped[str] = mapped_column(String(50), default="conversation")

    source_session_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Session ID where this fact was extracted"
    )

    related_fact_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    context_maps: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Metadata (renamed to avoid SQLAlchemy conflict)
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Fact(id={self.fact_id}, type={self.fact_type}, importance={self.importance})>"

    def to_dataclass(self) -> Fact:
        """Convert SQLAlchemy model to dataclass"""
        return Fact(
            fact_id=self.fact_id,
            text=self.text,
            thread_id=self.thread_id,
            ttl_days=self.ttl_days,
            importance=self.importance,
            confidence=self.confidence,
            tags=self.tags or [],
            created=self.created,
            updated=self.updated,
            last_accessed=self.last_accessed,
            fact_type=self.fact_type,
            needs_update=self.needs_update,
            update_frequency=self.update_frequency,
            source=self.source,
            related_fact_ids=self.related_fact_ids or [],
            context_maps=self.context_maps or [],
            meta_data=self.meta_data or {},
            usage_count=self.usage_count
        )


@dataclass
class ContextMap:
    """
    Context map for organizing related facts

    Example: "Trip to Athens" context map contains facts about
    dates, accommodation, weather, activities, etc.
    """

    map_id: str
    topic: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    fact_ids: List[str] = field(default_factory=list)
    sub_nodes: Dict[str, Any] = field(default_factory=dict)
    meta_data: Dict[str, Any] = field(default_factory=dict)


class ContextMapModel(Base):
    """
    SQLAlchemy model for context_maps table
    """
    __tablename__ = "context_maps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    map_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)

    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    fact_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    sub_nodes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<ContextMap(id={self.map_id}, topic={self.topic})>"

    def to_dataclass(self) -> ContextMap:
        """Convert SQLAlchemy model to dataclass"""
        return ContextMap(
            map_id=self.map_id,
            topic=self.topic,
            created=self.created,
            updated=self.updated,
            fact_ids=self.fact_ids or [],
            sub_nodes=self.sub_nodes or {},
            meta_data=self.meta_data or {}
        )


class AuditHistoryModel(Base):
    """
    Model for tracking memory audit history
    """
    __tablename__ = "audit_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    facts_analyzed: Mapped[int] = mapped_column(Integer)
    facts_kept: Mapped[int] = mapped_column(Integer)
    facts_updated: Mapped[int] = mapped_column(Integer)
    facts_deleted: Mapped[int] = mapped_column(Integer)

    report_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    execution_time_seconds: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"<AuditHistory(id={self.audit_id}, date={self.executed_at})>"
