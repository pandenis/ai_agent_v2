from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryEdge:
    """A directed relationship between two MemoryNodes in the memory graph."""

    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(
                f"weight must be between 0.0 and 1.0, got {self.weight}"
            )

    def __repr__(self) -> str:
        return f"MemoryEdge('{self.source_id}' -> '{self.target_id}', type='{self.edge_type}', weight={self.weight})"
