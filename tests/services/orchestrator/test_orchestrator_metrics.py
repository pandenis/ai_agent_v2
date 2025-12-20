"""
Tests for OrchestratorMetrics - Performance and cost tracking
"""
import pytest
from app.services.orchestrator.orchestrator_metrics import OrchestratorMetrics


class TestOrchestratorMetrics:
    """Tests for metrics tracking"""

    def test_metrics_class_exists(self):
        """Test: OrchestratorMetrics class can be instantiated"""
        metrics = OrchestratorMetrics()
        assert metrics is not None

    def test_track_query_stores_data(self):
        """Test: track_query stores metrics for a query"""
        metrics = OrchestratorMetrics()

        metrics.track_query(
            strategy="direct",
            elapsed_time_ms=50.5,
            cost_usd=0.0
        )

        stats = metrics.get_stats()
        assert stats["total_queries"] == 1
        assert stats["total_cost_usd"] == 0.0

    def test_track_multiple_queries(self):
        """Test: Multiple queries are tracked correctly"""
        metrics = OrchestratorMetrics()

        metrics.track_query(strategy="direct", elapsed_time_ms=50, cost_usd=0.0)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2500, cost_usd=0.0003)
        metrics.track_query(strategy="deep_reasoning", elapsed_time_ms=14000, cost_usd=0.005)

        stats = metrics.get_stats()
        assert stats["total_queries"] == 3
        assert stats["total_cost_usd"] == pytest.approx(0.0053, rel=0.01)

    def test_strategy_distribution(self):
        """Test: Track distribution of strategies used"""
        metrics = OrchestratorMetrics()

        metrics.track_query(strategy="direct", elapsed_time_ms=50, cost_usd=0.0)
        metrics.track_query(strategy="direct", elapsed_time_ms=45, cost_usd=0.0)
        metrics.track_query(strategy="enhanced", elapsed_time_ms=2500, cost_usd=0.0003)

        stats = metrics.get_stats()
        assert stats["strategy_counts"]["direct"] == 2
        assert stats["strategy_counts"]["enhanced"] == 1
        assert stats["strategy_counts"].get("deep_reasoning", 0) == 0

    def test_average_response_time(self):
        """Test: Calculate average response time"""
        metrics = OrchestratorMetrics()

        metrics.track_query(strategy="direct", elapsed_time_ms=100, cost_usd=0.0)
        metrics.track_query(strategy="direct", elapsed_time_ms=200, cost_usd=0.0)

        stats = metrics.get_stats()
        assert stats["avg_response_time_ms"] == 150.0

    def test_get_stats_empty_history(self):
        """Test: get_stats with no queries tracked"""
        metrics = OrchestratorMetrics()

        # No queries tracked
        stats = metrics.get_stats()

        assert stats["total_queries"] == 0
        assert stats["total_cost_usd"] == 0.0
        assert stats["avg_response_time_ms"] == 0.0

    def test_track_unknown_strategy(self):
        """Test: Track query with unknown strategy name"""
        metrics = OrchestratorMetrics()

        # Unknown strategy (edge case)
        metrics.track_query(
            strategy="custom_strategy",
            elapsed_time_ms=1000,
            cost_usd=0.001
        )

        stats = metrics.get_stats()
        assert stats["total_queries"] == 1
        assert stats["strategy_counts"]["custom_strategy"] == 1