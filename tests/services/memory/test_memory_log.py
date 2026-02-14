from datetime import datetime

from app.services.memory.memory_log import MemoryRetrievalLog, MemoryWriteLog


class TestMemoryRetrievalLog:
    def test_retrieval_log_creation_with_all_fields(self):
        # Arrange
        log = MemoryRetrievalLog(
            query="Where does user live?",
            nodes_scored=10,
            nodes_returned=3,
            nodes_dropped=7,
            dropped_node_ids=["n4", "n5", "n6", "n7", "n8", "n9", "n10"],
            top_scores=[("n1", 0.9), ("n2", 0.8), ("n3", 0.7)],
            token_budget=500,
            tokens_used=320,
            elapsed_ms=12.5,
            timestamp=datetime(2026, 2, 14),
        )

        # Assert
        assert log.query == "Where does user live?"
        assert log.nodes_scored == 10
        assert log.nodes_returned == 3
        assert log.nodes_dropped == 7
        assert log.dropped_node_ids == ["n4", "n5", "n6", "n7", "n8", "n9", "n10"]
        assert log.top_scores == [("n1", 0.9), ("n2", 0.8), ("n3", 0.7)]
        assert log.token_budget == 500
        assert log.tokens_used == 320
        assert log.elapsed_ms == 12.5
        assert log.timestamp == datetime(2026, 2, 14)

    def test_retrieval_log_default_timestamp(self):
        # Arrange
        now = datetime.utcnow()

        # Act
        log = MemoryRetrievalLog(
            query="test",
            nodes_scored=1,
            nodes_returned=1,
            nodes_dropped=0,
            dropped_node_ids=[],
            top_scores=[("n1", 0.5)],
            token_budget=500,
            tokens_used=10,
            elapsed_ms=1.0,
        )

        # Assert
        assert abs((log.timestamp - now).total_seconds()) < 1

    def test_retrieval_log_repr(self):
        # Arrange
        log = MemoryRetrievalLog(
            query="health info",
            nodes_scored=8,
            nodes_returned=3,
            nodes_dropped=5,
            dropped_node_ids=["n4", "n5", "n6", "n7", "n8"],
            top_scores=[("n1", 0.9), ("n2", 0.8), ("n3", 0.7)],
            token_budget=500,
            tokens_used=200,
            elapsed_ms=5.3,
        )

        # Act
        result = repr(log)

        # Assert
        assert "RetrievalLog" in result
        assert "health info" in result
        assert "3" in result
        assert "8" in result

    def test_retrieval_log_zero_results(self):
        # Arrange
        log = MemoryRetrievalLog(
            query="empty query",
            nodes_scored=0,
            nodes_returned=0,
            nodes_dropped=0,
            dropped_node_ids=[],
            top_scores=[],
            token_budget=500,
            tokens_used=0,
            elapsed_ms=0.1,
        )

        # Assert
        assert log.nodes_scored == 0
        assert log.nodes_returned == 0
        assert log.nodes_dropped == 0
        assert log.dropped_node_ids == []
        assert log.top_scores == []
        assert log.tokens_used == 0


class TestMemoryWriteLog:
    def test_write_log_creation_add_node(self):
        # Arrange
        log = MemoryWriteLog(
            operation="add_node",
            node_id="n1",
            reason="new fact extracted",
            dedup_detected=False,
            success=True,
        )

        # Assert
        assert log.operation == "add_node"
        assert log.node_id == "n1"
        assert log.reason == "new fact extracted"
        assert log.dedup_detected is False
        assert log.success is True
        assert log.target_id is None
        assert log.edge_type is None

    def test_write_log_creation_add_edge(self):
        # Arrange
        log = MemoryWriteLog(
            operation="add_edge",
            node_id="n1",
            target_id="n2",
            edge_type="related_to",
            reason="relationship found",
        )

        # Assert
        assert log.operation == "add_edge"
        assert log.node_id == "n1"
        assert log.target_id == "n2"
        assert log.edge_type == "related_to"
        assert log.reason == "relationship found"

    def test_write_log_creation_remove_node(self):
        # Arrange
        log = MemoryWriteLog(
            operation="remove_node",
            node_id="n5",
            reason="expired TTL",
        )

        # Assert
        assert log.operation == "remove_node"
        assert log.success is True

    def test_write_log_dedup_detected(self):
        # Arrange
        log = MemoryWriteLog(
            operation="add_node",
            node_id="n1",
            dedup_detected=True,
            success=False,
            reason="duplicate node ID",
        )

        # Assert
        assert log.dedup_detected is True
        assert log.success is False

    def test_write_log_repr(self):
        # Arrange
        log = MemoryWriteLog(operation="add_node", node_id="n3", dedup_detected=False)

        # Act
        result = repr(log)

        # Assert
        assert "WriteLog" in result
        assert "add_node" in result
        assert "n3" in result
