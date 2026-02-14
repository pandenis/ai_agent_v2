from dataclasses import dataclass, field
from datetime import datetime
from math import exp


@dataclass
class MemoryNode:
    """A node in the graph-based memory map representing a single memory unit."""

    id: str
    content: str
    node_type: str
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0

    def __post_init__(self):
        if not (0.0 <= self.importance <= 1.0):
            raise ValueError(
                f"importance must be between 0.0 and 1.0, got {self.importance}"
            )

    def calculate_weight(self) -> float:
        """Calculate a composite relevance score from recency, importance, and access frequency.

        Formula: 0.4 * recency + 0.4 * importance + 0.2 * access_frequency

        - recency_score: exponential decay based on days since last access (half-life ~5 days)
        - importance_score: the node's importance value (0.0-1.0)
        - access_score: access_count / 20, capped at 1.0
        """
        days_since_access = (datetime.utcnow() - self.last_accessed).total_seconds() / 86400.0
        recency_score = exp(-days_since_access / 7.0)
        importance_score = self.importance
        access_score = min(self.access_count / 20.0, 1.0)
        weight = 0.4 * recency_score + 0.4 * importance_score + 0.2 * access_score
        return max(0.0, min(1.0, weight))

    def __repr__(self) -> str:
        return f"MemoryNode(id='{self.id}', type='{self.node_type}', content='{self.content[:50]}')"
