from datetime import datetime

import pytest

from app.services.memory.memory_edge import MemoryEdge


class TestMemoryEdge:
    def test_memory_edge_creation_with_all_fields(self):
        # Arrange
        source_id = "node1"
        target_id = "node2"
        edge_type = "related_to"
        weight = 0.9
        created_at = datetime(2026, 2, 1)

        # Act
        edge = MemoryEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            created_at=created_at,
        )

        # Assert
        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.edge_type == "related_to"
        assert edge.weight == 0.9
        assert edge.created_at == datetime(2026, 2, 1)

    def test_memory_edge_default_values(self):
        # Arrange
        now = datetime.utcnow()

        # Act
        edge = MemoryEdge(
            source_id="node1",
            target_id="node2",
            edge_type="supports",
        )

        # Assert
        assert edge.weight == 1.0
        assert abs((edge.created_at - now).total_seconds()) < 1

    def test_memory_edge_different_types(self):
        # Arrange
        test_cases = [
            ("node_paris", "node_cuisine", "related_to"),
            ("node_vegetarian", "node_steak", "contradicts"),
            ("node_doctor", "node_prescription", "supports"),
            ("node_trip", "node_booking", "caused_by"),
            ("node_doctor_visit", "node_medication", "follows"),
        ]

        for source_id, target_id, edge_type in test_cases:
            # Act
            edge = MemoryEdge(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
            )

            # Assert
            assert edge.edge_type == edge_type

    def test_memory_edge_weight_validation(self):
        # Arrange / Act / Assert — invalid weights
        with pytest.raises(ValueError):
            MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=-0.1)

        with pytest.raises(ValueError):
            MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=1.1)

        # Arrange / Act — boundary values
        edge_zero = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.0)
        edge_one = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=1.0)

        # Assert
        assert edge_zero.weight == 0.0
        assert edge_one.weight == 1.0

    def test_memory_edge_repr(self):
        # Arrange
        edge = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to")

        # Act
        result = repr(edge)

        # Assert
        assert "MemoryEdge" in result
        assert "n1" in result
        assert "n2" in result
        assert "related_to" in result
