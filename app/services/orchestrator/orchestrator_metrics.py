"""
OrchestratorMetrics - Performance and cost tracking for orchestrator.

Tracks:
- Query counts by strategy
- Response times
- Costs
- Performance targets

Usage:
    >>> metrics = OrchestratorMetrics()
    >>> metrics.track_query(strategy="direct", elapsed_time_ms=50, cost_usd=0.0)
    >>> stats = metrics.get_stats()
    >>> print(f"Total queries: {stats['total_queries']}")
"""
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime


@dataclass
class QueryRecord:
    """Single query record"""
    strategy: str
    elapsed_time_ms: float
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class OrchestratorMetrics:
    """Tracks orchestrator performance metrics"""

    # Performance targets (ms)
    PERFORMANCE_TARGETS = {
        "direct": 200,  # Should be < 200ms
        "enhanced": 5000,  # Should be < 5s
        "deep_reasoning": 20000  # Should be < 20s
    }

    def __init__(self):
        self._history: List[QueryRecord] = []
        self._strategy_counts: Dict[str, int] = {
            "direct": 0,
            "enhanced": 0,
            "deep_reasoning": 0
        }

    def track_query(
            self,
            strategy: str,
            elapsed_time_ms: float,
            cost_usd: float
    ) -> None:
        """
        Track a query's metrics.

        Args:
            strategy: "direct", "enhanced", or "deep_reasoning"
            elapsed_time_ms: Response time in milliseconds
            cost_usd: Cost in USD
        """
        record = QueryRecord(
            strategy=strategy,
            elapsed_time_ms=elapsed_time_ms,
            cost_usd=cost_usd
        )
        self._history.append(record)

        # Update strategy count
        if strategy in self._strategy_counts:
            self._strategy_counts[strategy] += 1
        else:
            self._strategy_counts[strategy] = 1

    def get_stats(self) -> Dict:
        """
        Get aggregated statistics.

        Returns:
            Dictionary with metrics summary
        """
        if not self._history:
            return {
                "total_queries": 0,
                "total_cost_usd": 0.0,
                "avg_response_time_ms": 0.0,
                "strategy_counts": self._strategy_counts.copy()
            }

        total_queries = len(self._history)
        total_cost = sum(r.cost_usd for r in self._history)
        avg_time = sum(r.elapsed_time_ms for r in self._history) / total_queries

        return {
            "total_queries": total_queries,
            "total_cost_usd": total_cost,
            "avg_response_time_ms": avg_time,
            "strategy_counts": self._strategy_counts.copy()
        }