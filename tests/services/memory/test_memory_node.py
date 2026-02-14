from datetime import datetime, timedelta

from app.services.memory.memory_node import MemoryNode


class TestMemoryNode:
    def test_memory_node_creation_with_all_fields(self):
        # Arrange
        node_id = "node1"
        content = "User lives in Paris"
        node_type = "fact"
        importance = 0.8
        created_at = datetime(2026, 1, 1)
        last_accessed = datetime(2026, 2, 1)

        # Act
        node = MemoryNode(
            id=node_id,
            content=content,
            node_type=node_type,
            importance=importance,
            created_at=created_at,
            last_accessed=last_accessed,
        )

        # Assert
        assert node.id == "node1"
        assert node.content == "User lives in Paris"
        assert node.node_type == "fact"
        assert node.importance == 0.8
        assert node.created_at == datetime(2026, 1, 1)
        assert node.last_accessed == datetime(2026, 2, 1)

    def test_memory_node_default_values(self):
        # Arrange
        now = datetime.utcnow()

        # Act
        node = MemoryNode(
            id="node2",
            content="Prefers warm weather",
            node_type="preference",
        )

        # Assert
        assert node.importance == 0.5
        assert abs((node.created_at - now).total_seconds()) < 1
        assert abs((node.last_accessed - now).total_seconds()) < 1

    def test_memory_node_different_types(self):
        # Arrange
        test_cases = [
            ("fact", "Capital of France is Paris"),
            ("preference", "User is vegetarian"),
            ("episode", "Visited doctor on Monday"),
            ("context", "Currently planning a trip to Japan"),
        ]

        for node_type, content in test_cases:
            # Act
            node = MemoryNode(
                id=f"node_{node_type}",
                content=content,
                node_type=node_type,
            )

            # Assert
            assert node.node_type == node_type

    def test_memory_node_repr(self):
        # Arrange
        node = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")

        # Act
        result = repr(node)

        # Assert
        assert "MemoryNode" in result
        assert "n1" in result
        assert "fact" in result

    def test_calculate_weight_recent_high_importance(self):
        # Arrange
        node = MemoryNode(
            id="n1",
            content="Important recent memory",
            node_type="fact",
            importance=0.9,
            last_accessed=datetime.utcnow(),
            access_count=10,
        )

        # Act
        weight = node.calculate_weight()

        # Assert
        assert 0.8 <= weight <= 1.0

    def test_calculate_weight_old_low_importance(self):
        # Arrange
        node = MemoryNode(
            id="n1",
            content="Old unimportant memory",
            node_type="fact",
            importance=0.1,
            last_accessed=datetime.utcnow() - timedelta(days=30),
            access_count=1,
        )

        # Act
        weight = node.calculate_weight()

        # Assert
        assert 0.0 <= weight <= 0.3

    def test_calculate_weight_recent_beats_old(self):
        # Arrange
        node_recent = MemoryNode(
            id="n1",
            content="Recent memory",
            node_type="fact",
            importance=0.5,
            last_accessed=datetime.utcnow(),
            access_count=5,
        )
        node_old = MemoryNode(
            id="n2",
            content="Old memory",
            node_type="fact",
            importance=0.5,
            last_accessed=datetime.utcnow() - timedelta(days=14),
            access_count=5,
        )

        # Act / Assert
        assert node_recent.calculate_weight() > node_old.calculate_weight()

    def test_calculate_weight_high_importance_beats_low(self):
        # Arrange
        now = datetime.utcnow()
        node_high = MemoryNode(
            id="n1",
            content="High importance",
            node_type="fact",
            importance=0.9,
            last_accessed=now,
            access_count=5,
        )
        node_low = MemoryNode(
            id="n2",
            content="Low importance",
            node_type="fact",
            importance=0.2,
            last_accessed=now,
            access_count=5,
        )

        # Act / Assert
        assert node_high.calculate_weight() > node_low.calculate_weight()

    def test_calculate_weight_frequently_accessed_beats_rare(self):
        # Arrange
        now = datetime.utcnow()
        node_frequent = MemoryNode(
            id="n1",
            content="Frequently accessed",
            node_type="fact",
            importance=0.5,
            last_accessed=now,
            access_count=20,
        )
        node_rare = MemoryNode(
            id="n2",
            content="Rarely accessed",
            node_type="fact",
            importance=0.5,
            last_accessed=now,
            access_count=1,
        )

        # Act / Assert
        assert node_frequent.calculate_weight() > node_rare.calculate_weight()

    def test_calculate_weight_returns_between_zero_and_one(self):
        # Arrange
        nodes = [
            MemoryNode(
                id="n1",
                content="Worst case",
                node_type="fact",
                importance=0.0,
                last_accessed=datetime.utcnow() - timedelta(days=90),
                access_count=0,
            ),
            MemoryNode(
                id="n2",
                content="Best case",
                node_type="fact",
                importance=1.0,
                last_accessed=datetime.utcnow(),
                access_count=100,
            ),
        ]

        # Act / Assert
        for node in nodes:
            weight = node.calculate_weight()
            assert 0.0 <= weight <= 1.0

    def test_calculate_weight_default_access_count(self):
        # Arrange
        node = MemoryNode(id="n1", content="Default access", node_type="fact")

        # Act / Assert
        assert node.access_count == 0
        weight = node.calculate_weight()
        assert isinstance(weight, float)
        assert 0.0 <= weight <= 1.0
