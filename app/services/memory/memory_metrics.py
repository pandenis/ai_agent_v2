"""In-memory metrics collector for MemoryMap operations.

Tracks aggregate statistics across retrieval and write operations
without persisting to disk. Designed for observability via debug endpoints.
"""

from typing import Any, Dict

from app.services.memory.memory_log import MemoryRetrievalLog, MemoryWriteLog


class MemoryMetrics:
    """Collects cumulative metrics on memory retrieval and write operations."""

    def __init__(self):
        """Initialize all counters to zero."""
        self.total_retrievals: int = 0
        self.total_writes: int = 0
        self.total_nodes_scored: int = 0
        self.total_nodes_returned: int = 0
        self.total_retrieval_ms: float = 0.0
        self.total_write_ops_by_type: Dict[str, int] = {
            "add_node": 0,
            "add_edge": 0,
            "remove_node": 0,
        }
        self.total_dedup_detections: int = 0

    def record_retrieval(self, log: MemoryRetrievalLog) -> None:
        """Record a retrieval operation from its log entry."""
        self.total_retrievals += 1
        self.total_nodes_scored += log.nodes_scored
        self.total_nodes_returned += log.nodes_returned
        self.total_retrieval_ms += log.elapsed_ms

    def record_write(self, log: MemoryWriteLog) -> None:
        """Record a write operation from its log entry."""
        self.total_writes += 1
        if log.operation in self.total_write_ops_by_type:
            self.total_write_ops_by_type[log.operation] += 1
        if log.dedup_detected:
            self.total_dedup_detections += 1

    @property
    def avg_retrieval_ms(self) -> float:
        """Average elapsed time per retrieval in milliseconds."""
        if self.total_retrievals > 0:
            return self.total_retrieval_ms / self.total_retrievals
        return 0.0

    @property
    def avg_nodes_returned(self) -> float:
        """Average number of nodes returned per retrieval."""
        if self.total_retrievals > 0:
            return self.total_nodes_returned / self.total_retrievals
        return 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Return a dict with all fields and computed averages."""
        return {
            "total_retrievals": self.total_retrievals,
            "total_writes": self.total_writes,
            "total_nodes_scored": self.total_nodes_scored,
            "total_nodes_returned": self.total_nodes_returned,
            "avg_retrieval_ms": self.avg_retrieval_ms,
            "avg_nodes_returned": self.avg_nodes_returned,
            "total_write_ops_by_type": dict(self.total_write_ops_by_type),
            "total_dedup_detections": self.total_dedup_detections,
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.total_retrievals = 0
        self.total_writes = 0
        self.total_nodes_scored = 0
        self.total_nodes_returned = 0
        self.total_retrieval_ms = 0.0
        self.total_write_ops_by_type = {
            "add_node": 0,
            "add_edge": 0,
            "remove_node": 0,
        }
        self.total_dedup_detections = 0
