"""Pydantic response models for debug endpoints."""

from typing import Dict, List, Optional

from pydantic import BaseModel


class MemoryNodeDebug(BaseModel):
    """Serialized view of a single MemoryNode for debug inspection."""

    id: str
    content: str
    node_type: str
    importance: float
    access_count: int
    weight: float


class MemoryEdgeDebug(BaseModel):
    """Serialized view of a single MemoryEdge for debug inspection."""

    source_id: str
    target_id: str
    edge_type: str
    weight: float


class RetrievalLogDebug(BaseModel):
    """Serialized view of a single MemoryRetrievalLog for debug inspection."""

    query: str
    nodes_scored: int
    nodes_returned: int
    nodes_dropped: int
    tokens_used: int
    elapsed_ms: float
    timestamp: str


class WriteLogDebug(BaseModel):
    """Serialized view of a single MemoryWriteLog for debug inspection."""

    operation: str
    node_id: str
    target_id: Optional[str] = None
    edge_type: Optional[str] = None
    dedup_detected: bool
    success: bool
    timestamp: str


class EnrichedGraphStats(BaseModel):
    """Graph statistics enriched with computed averages."""

    node_count: int
    edge_count: int
    avg_importance: float
    avg_weight: float


class MemoryMetricsResponse(BaseModel):
    """Aggregate metrics for memory operations."""

    total_retrievals: int
    total_writes: int
    total_nodes_scored: int
    total_nodes_returned: int
    avg_retrieval_ms: float
    avg_nodes_returned: float
    total_write_ops_by_type: Dict[str, int]
    total_dedup_detections: int


class MemoryDebugResponse(BaseModel):
    """Full debug response for a session's MemoryMap."""

    session_id: str
    graph_stats: EnrichedGraphStats
    nodes: List[MemoryNodeDebug]
    edges: List[MemoryEdgeDebug]
    recent_retrievals: List[RetrievalLogDebug] = []
    recent_writes: List[WriteLogDebug] = []
