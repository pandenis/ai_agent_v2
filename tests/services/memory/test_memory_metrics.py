"""Tests for MemoryMetrics aggregate statistics collector."""

from app.services.memory.memory_log import MemoryRetrievalLog, MemoryWriteLog
from app.services.memory.memory_metrics import MemoryMetrics


class TestMemoryMetrics:
    def test_metrics_initial_state(self):
        """A fresh MemoryMetrics has all counters at zero."""
        # Arrange
        metrics = MemoryMetrics()

        # Assert
        assert metrics.total_retrievals == 0
        assert metrics.total_writes == 0
        assert metrics.avg_retrieval_ms == 0.0
        assert metrics.avg_nodes_returned == 0.0

    def test_record_retrieval_updates_counters(self):
        """Recording a retrieval log increments all retrieval counters."""
        # Arrange
        metrics = MemoryMetrics()
        log = MemoryRetrievalLog(
            query="test", nodes_scored=10, nodes_returned=3,
            nodes_dropped=7, dropped_node_ids=[], top_scores=[],
            token_budget=500, tokens_used=200, elapsed_ms=15.5,
        )

        # Act
        metrics.record_retrieval(log)

        # Assert
        assert metrics.total_retrievals == 1
        assert metrics.total_nodes_scored == 10
        assert metrics.total_nodes_returned == 3
        assert metrics.total_retrieval_ms == 15.5

    def test_record_multiple_retrievals_averages(self):
        """Averages are computed correctly across multiple retrievals."""
        # Arrange
        metrics = MemoryMetrics()
        for elapsed, returned in [(10.0, 2), (20.0, 4), (30.0, 6)]:
            log = MemoryRetrievalLog(
                query="q", nodes_scored=5, nodes_returned=returned,
                nodes_dropped=0, dropped_node_ids=[], top_scores=[],
                token_budget=500, tokens_used=100, elapsed_ms=elapsed,
            )
            metrics.record_retrieval(log)

        # Assert
        assert metrics.total_retrievals == 3
        assert metrics.avg_retrieval_ms == 20.0
        assert metrics.avg_nodes_returned == 4.0

    def test_record_write_updates_counters(self):
        """Recording write logs increments per-operation type counters."""
        # Arrange
        metrics = MemoryMetrics()
        logs = [
            MemoryWriteLog(operation="add_node", node_id="n1"),
            MemoryWriteLog(operation="add_node", node_id="n2"),
            MemoryWriteLog(operation="add_edge", node_id="n1", target_id="n2", edge_type="related_to"),
        ]

        # Act
        for log in logs:
            metrics.record_write(log)

        # Assert
        assert metrics.total_writes == 3
        assert metrics.total_write_ops_by_type["add_node"] == 2
        assert metrics.total_write_ops_by_type["add_edge"] == 1
        assert metrics.total_write_ops_by_type["remove_node"] == 0

    def test_record_write_tracks_dedup(self):
        """Dedup detections are counted separately."""
        # Arrange
        metrics = MemoryMetrics()
        logs = [
            MemoryWriteLog(operation="add_node", node_id="n1", dedup_detected=False),
            MemoryWriteLog(operation="add_node", node_id="n1", dedup_detected=True, success=False),
        ]

        # Act
        for log in logs:
            metrics.record_write(log)

        # Assert
        assert metrics.total_dedup_detections == 1

    def test_get_summary_returns_complete_dict(self):
        """get_summary() returns a dict with all expected keys."""
        # Arrange
        metrics = MemoryMetrics()
        metrics.record_retrieval(MemoryRetrievalLog(
            query="q", nodes_scored=5, nodes_returned=2,
            nodes_dropped=3, dropped_node_ids=[], top_scores=[],
            token_budget=500, tokens_used=100, elapsed_ms=10.0,
        ))
        metrics.record_write(MemoryWriteLog(operation="add_node", node_id="n1"))
        metrics.record_write(MemoryWriteLog(operation="add_edge", node_id="n1", target_id="n2"))

        # Act
        summary = metrics.get_summary()

        # Assert
        expected_keys = {
            "total_retrievals", "total_writes", "total_nodes_scored",
            "total_nodes_returned", "avg_retrieval_ms", "avg_nodes_returned",
            "total_write_ops_by_type", "total_dedup_detections",
        }
        assert expected_keys == set(summary.keys())

    def test_reset_clears_all_counters(self):
        """reset() brings all counters back to zero."""
        # Arrange
        metrics = MemoryMetrics()
        metrics.record_retrieval(MemoryRetrievalLog(
            query="q", nodes_scored=5, nodes_returned=2,
            nodes_dropped=3, dropped_node_ids=[], top_scores=[],
            token_budget=500, tokens_used=100, elapsed_ms=10.0,
        ))
        metrics.record_write(MemoryWriteLog(
            operation="add_node", node_id="n1", dedup_detected=True,
        ))

        # Act
        metrics.reset()

        # Assert
        assert metrics.total_retrievals == 0
        assert metrics.total_writes == 0
        assert metrics.total_dedup_detections == 0
        assert metrics.avg_retrieval_ms == 0.0
