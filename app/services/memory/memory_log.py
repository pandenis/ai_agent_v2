from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class MemoryRetrievalLog:
    """Captures a single memory retrieval operation for observability and debugging."""

    query: str
    nodes_scored: int
    nodes_returned: int
    nodes_dropped: int
    dropped_node_ids: List[str]
    top_scores: List[Tuple[str, float]]
    token_budget: int
    tokens_used: int
    elapsed_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"RetrievalLog(query='{self.query}', "
            f"returned={self.nodes_returned}/{self.nodes_scored}, "
            f"elapsed={self.elapsed_ms:.1f}ms)"
        )


@dataclass
class MemoryWriteLog:
    """Captures a single memory mutation (add/remove node or edge) for observability."""

    operation: str
    node_id: str
    target_id: Optional[str] = None
    edge_type: Optional[str] = None
    reason: str = ""
    dedup_detected: bool = False
    success: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        return f"WriteLog(op='{self.operation}', node='{self.node_id}', dedup={self.dedup_detected})"
