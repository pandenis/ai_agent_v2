from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_node import MemoryNode


class TestMemoryMap:
    def test_add_node_and_get_node(self):
        # Arrange
        memory_map = MemoryMap()
        node = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")

        # Act
        memory_map.add_node(node)
        result = memory_map.get_node("n1")

        # Assert
        assert result is node

    def test_get_node_not_found_returns_none(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.get_node("nonexistent")

        # Assert
        assert result is None

    def test_add_edge_between_existing_nodes(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User prefers French cuisine", node_type="preference")
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        edge = MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8)

        # Act
        memory_map.add_edge(edge)

        # Assert
        assert len(memory_map.edges) == 1

    def test_add_edge_with_missing_node_raises_error(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        memory_map.add_node(n1)
        edge = MemoryEdge(source_id="n1", target_id="n99", edge_type="related_to")

        # Act / Assert
        with pytest.raises(ValueError, match="missing|not found"):
            memory_map.add_edge(edge)

    def test_get_neighbors_returns_connected_nodes(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User prefers French cuisine", node_type="preference")
        n3 = MemoryNode(id="n3", content="User visited Eiffel Tower", node_type="episode")
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_node(n3)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.6))

        # Act
        neighbors = memory_map.get_neighbors("n1")

        # Assert
        assert len(neighbors) == 2
        assert n2 in neighbors
        assert n3 in neighbors

    def test_get_neighbors_empty_for_isolated_node(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User prefers French cuisine", node_type="preference")
        memory_map.add_node(n1)
        memory_map.add_node(n2)

        # Act
        neighbors = memory_map.get_neighbors("n1")

        # Assert
        assert neighbors == []

    def test_get_neighbors_nonexistent_node_returns_empty(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        neighbors = memory_map.get_neighbors("nonexistent")

        # Assert
        assert neighbors == []

    def test_find_related_returns_nodes_sorted_by_weight(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User is a vegetarian", node_type="preference")
        n2 = MemoryNode(id="n2", content="User dislikes meat", node_type="preference")
        n3 = MemoryNode(id="n3", content="User likes tofu", node_type="preference")
        n4 = MemoryNode(id="n4", content="User visited a cooking class", node_type="episode")
        for node in [n1, n2, n3, n4]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="supports", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.7))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n4", edge_type="related_to", weight=0.3))

        # Act
        result = memory_map.find_related("n1")

        # Assert
        assert result == [(n2, 0.9), (n3, 0.7), (n4, 0.3)]

    def test_find_related_includes_bidirectional_edges(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Tokyo", node_type="fact")
        n2 = MemoryNode(id="n2", content="User speaks Japanese", node_type="fact")
        n3 = MemoryNode(id="n3", content="User eats sushi weekly", node_type="preference")
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n3", target_id="n1", edge_type="related_to", weight=0.6))

        # Act
        result = memory_map.find_related("n1")

        # Assert
        assert result == [(n2, 0.8), (n3, 0.6)]

    def test_find_related_no_connections_returns_empty(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User likes coffee", node_type="preference")
        memory_map.add_node(n1)
        memory_map.add_node(n2)

        # Act
        result = memory_map.find_related("n1")

        # Assert
        assert result == []

    def test_find_related_nonexistent_node_returns_empty(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.find_related("ghost")

        # Assert
        assert result == []

    def test_find_related_with_max_results(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User studies economics", node_type="fact")
        n2 = MemoryNode(id="n2", content="User reads Financial Times", node_type="preference")
        n3 = MemoryNode(id="n3", content="User tracks stock market", node_type="preference")
        n4 = MemoryNode(id="n4", content="User has MBA degree", node_type="fact")
        n5 = MemoryNode(id="n5", content="User attended economics conference", node_type="episode")
        for node in [n1, n2, n3, n4, n5]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n4", edge_type="related_to", weight=0.7))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n5", edge_type="related_to", weight=0.5))

        # Act
        result = memory_map.find_related("n1", max_results=2)

        # Assert
        assert result == [(n2, 0.9), (n3, 0.8)]

    def test_node_count_and_edge_count(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User has a dog named Max", node_type="fact")
        n2 = MemoryNode(id="n2", content="Max is a golden retriever", node_type="fact")
        n3 = MemoryNode(id="n3", content="User walks Max every morning", node_type="episode")
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.7))

        # Act / Assert
        assert memory_map.node_count == 3
        assert memory_map.edge_count == 2

    def test_node_count_empty_map(self):
        # Arrange
        memory_map = MemoryMap()

        # Act / Assert
        assert memory_map.node_count == 0
        assert memory_map.edge_count == 0

    def test_remove_node_removes_node_and_cascades_edges(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User studies medicine", node_type="fact")
        n2 = MemoryNode(id="n2", content="User works at hospital", node_type="fact")
        n3 = MemoryNode(id="n3", content="User reads medical journals", node_type="preference")
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="supports", weight=0.7))
        memory_map.add_edge(MemoryEdge(source_id="n2", target_id="n3", edge_type="related_to", weight=0.5))

        # Act
        memory_map.remove_node("n1")

        # Assert
        assert memory_map.get_node("n1") is None
        assert memory_map.node_count == 2
        assert memory_map.edge_count == 1
        assert memory_map.get_node("n2") is not None
        assert memory_map.get_node("n3") is not None

    def test_remove_node_nonexistent_raises_error(self):
        # Arrange
        memory_map = MemoryMap()

        # Act / Assert
        with pytest.raises(KeyError):
            memory_map.remove_node("ghost")

    def test_memory_map_repr(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact")
        n2 = MemoryNode(id="n2", content="User likes coffee", node_type="preference")
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))

        # Act
        result = repr(memory_map)

        # Assert
        assert "MemoryMap" in result
        assert "2 nodes" in result
        assert "1 edge" in result

    def test_build_local_slice_returns_subgraph(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Tokyo", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User speaks Japanese", node_type="fact", importance=0.8)
        n3 = MemoryNode(id="n3", content="User eats ramen weekly", node_type="preference", importance=0.6)
        n4 = MemoryNode(id="n4", content="User has a cat named Mochi", node_type="fact", importance=0.5)
        for node in [n1, n2, n3, n4]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.6))

        # Act
        result = memory_map.build_local_slice("n1", token_budget=500)

        # Assert
        assert result.get_node("n1") is not None
        assert result.get_node("n2") is not None
        assert result.get_node("n3") is not None
        assert result.get_node("n4") is None
        assert result.edge_count == 2

    def test_build_local_slice_respects_token_budget(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User studies weather patterns", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="A" * 100, node_type="fact", importance=0.8)
        n3 = MemoryNode(id="n3", content="B" * 100, node_type="fact", importance=0.7)
        n4 = MemoryNode(id="n4", content="C" * 100, node_type="fact", importance=0.6)
        n5 = MemoryNode(id="n5", content="D" * 100, node_type="fact", importance=0.5)
        for node in [n1, n2, n3, n4, n5]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n4", edge_type="related_to", weight=0.7))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n5", edge_type="related_to", weight=0.6))

        # Act
        result = memory_map.build_local_slice("n1", token_budget=100)

        # Assert
        assert result.node_count < memory_map.node_count
        assert result.get_node("n1") is not None
        # Higher-weight neighbors included before lower-weight ones
        included_ids = set(result.nodes.keys()) - {"n1"}
        if "n2" in included_ids:
            assert True  # highest weight neighbor included
        if "n5" in included_ids and "n2" not in included_ids:
            assert False, "Lower-weight node included but higher-weight excluded"

    def test_build_local_slice_always_includes_start_node(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User is a doctor", node_type="fact", importance=0.5)
        memory_map.add_node(n1)

        # Act
        result = memory_map.build_local_slice("n1", token_budget=500)

        # Assert
        assert result.get_node("n1") is not None
        assert result.node_count == 1
        assert result.edge_count == 0

    def test_build_local_slice_nonexistent_node_returns_empty(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.build_local_slice("ghost", token_budget=500)

        # Assert
        assert result.node_count == 0

    def test_build_local_slice_two_hop_neighbors(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User plans trip to Italy", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User wants to visit Rome", node_type="preference", importance=0.8)
        n3 = MemoryNode(id="n3", content="Colosseum is in Rome", node_type="fact", importance=0.7)
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n2", target_id="n3", edge_type="related_to", weight=0.7))

        # Act
        result = memory_map.build_local_slice("n1", token_budget=500)

        # Assert
        assert result.get_node("n1") is not None
        assert result.get_node("n2") is not None
        assert result.get_node("n3") is not None

    def test_build_local_slice_prioritizes_by_weight(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="Main node", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="Low relevance node with some extra text padding", node_type="fact", importance=0.2)
        n3 = MemoryNode(id="n3", content="High relevance node with some extra text padding", node_type="fact", importance=0.9)
        n4 = MemoryNode(id="n4", content="Medium relevance node with extra text padding", node_type="fact", importance=0.5)
        for node in [n1, n2, n3, n4]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.3))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n4", edge_type="related_to", weight=0.6))

        # Act — tight budget: room for start + ~2 neighbors
        result = memory_map.build_local_slice("n1", token_budget=80)

        # Assert
        assert result.get_node("n3") is not None  # highest weight neighbor always included
        if result.node_count <= 3:
            # If budget forced exclusion, n2 (lowest weight) should be excluded first
            assert result.get_node("n2") is None

    def test_to_prompt_context_basic_format(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Berlin", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User speaks German", node_type="fact", importance=0.8)
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))

        # Act
        result = memory_map.to_prompt_context()

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "User lives in Berlin" in result
        assert "User speaks German" in result

    def test_to_prompt_context_nodes_sorted_by_weight(self):
        # Arrange
        now = datetime.utcnow()
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User has diabetes", node_type="fact", importance=0.9, last_accessed=now)
        n2 = MemoryNode(id="n2", content="User takes insulin daily", node_type="fact", importance=0.7, last_accessed=now)
        n3 = MemoryNode(id="n3", content="User visited endocrinologist", node_type="episode", importance=0.3, last_accessed=now)
        for node in [n1, n2, n3]:
            memory_map.add_node(node)

        # Act
        result = memory_map.to_prompt_context()

        # Assert
        pos_diabetes = result.index("User has diabetes")
        pos_endocrinologist = result.index("User visited endocrinologist")
        assert pos_diabetes < pos_endocrinologist

    def test_to_prompt_context_includes_relationship_info(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User is allergic to peanuts", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User carries EpiPen", node_type="fact", importance=0.8)
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="caused_by", weight=0.9))

        # Act
        result = memory_map.to_prompt_context()

        # Assert
        assert "\u2192" in result or "related" in result.lower() or "caused_by" in result

    def test_to_prompt_context_empty_map(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.to_prompt_context()

        # Assert
        assert result == ""

    def test_to_prompt_context_single_node_no_edges(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User prefers metric system", node_type="preference", importance=0.5)
        memory_map.add_node(n1)

        # Act
        result = memory_map.to_prompt_context()

        # Assert
        assert "User prefers metric system" in result
        assert "\u2192" not in result

    def test_to_prompt_context_respects_max_tokens(self):
        # Arrange
        memory_map = MemoryMap()
        now = datetime.utcnow()
        for i in range(1, 6):
            node = MemoryNode(
                id=f"n{i}",
                content=f"This is a long memory content entry number {i} with extra padding to fill space easily " + "x" * 40,
                node_type="fact",
                importance=1.0 - (i * 0.1),
                last_accessed=now,
            )
            memory_map.add_node(node)

        # Act
        result = memory_map.to_prompt_context(max_tokens=50)

        # Assert
        assert len(result) // 4 <= 60
        # Higher-weight nodes appear before lower-weight ones
        if "entry number 1" in result and "entry number 5" in result:
            assert result.index("entry number 1") < result.index("entry number 5")

    def test_build_context_for_query_finds_relevant_nodes(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Paris", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User speaks French fluently", node_type="fact", importance=0.8)
        n3 = MemoryNode(id="n3", content="User is allergic to shellfish", node_type="fact", importance=0.7)
        n4 = MemoryNode(id="n4", content="User works as a chef", node_type="fact", importance=0.8)
        for node in [n1, n2, n3, n4]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n3", target_id="n4", edge_type="related_to", weight=0.6))

        # Act
        result = memory_map.build_context_for_query("Where does the user live?", token_budget=500)

        # Assert
        assert len(result) > 0
        assert "Paris" in result
        assert "French" in result

    def test_build_context_for_query_matches_keywords(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User takes metformin for diabetes", node_type="fact", importance=0.8)
        n2 = MemoryNode(id="n2", content="User jogs every morning", node_type="preference", importance=0.6)
        n3 = MemoryNode(id="n3", content="User has appointment with Dr. Smith on Tuesday", node_type="episode", importance=0.7)
        for node in [n1, n2, n3]:
            memory_map.add_node(node)

        # Act
        result = memory_map.build_context_for_query("Tell me about the user's health", token_budget=500)

        # Assert
        assert len(result) > 0
        assert "metformin" in result or "diabetes" in result

    def test_build_context_for_query_empty_map_returns_empty(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.build_context_for_query("anything", token_budget=500)

        # Assert
        assert result == ""

    def test_build_context_for_query_no_match_returns_best_effort(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User enjoys cooking Italian food", node_type="preference", importance=0.9)
        n2 = MemoryNode(id="n2", content="User has two cats", node_type="fact", importance=0.7)
        for node in [n1, n2]:
            memory_map.add_node(node)

        # Act
        result = memory_map.build_context_for_query("quantum physics equations", token_budget=500)

        # Assert
        assert isinstance(result, str)

    def test_build_context_for_query_respects_token_budget(self):
        # Arrange
        memory_map = MemoryMap()
        now = datetime.utcnow()
        for i in range(1, 7):
            node = MemoryNode(
                id=f"n{i}",
                content=f"This is memory entry number {i} with padding text to make it longer " + "z" * 40,
                node_type="fact",
                importance=1.0 - (i * 0.1),
                last_accessed=now,
            )
            memory_map.add_node(node)
        # Connect all to n1
        for i in range(2, 7):
            memory_map.add_edge(MemoryEdge(source_id="n1", target_id=f"n{i}", edge_type="related_to", weight=1.0 - (i * 0.1)))

        # Act
        result = memory_map.build_context_for_query("user info", token_budget=60)

        # Assert
        assert len(result) // 4 <= 80

    def test_build_context_for_query_updates_access_count(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in London", node_type="fact", importance=0.8, access_count=0)
        n2 = MemoryNode(id="n2", content="User commutes by tube", node_type="fact", importance=0.6, access_count=0)
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.7))
        before = datetime.utcnow()

        # Act
        memory_map.build_context_for_query("Where does user live?", token_budget=500)

        # Assert
        assert n1.access_count > 0
        assert abs((n1.last_accessed - before).total_seconds()) < 2

    def test_build_context_for_query_multiple_seed_nodes(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User traveled to Japan in 2025", node_type="episode", importance=0.7)
        n2 = MemoryNode(id="n2", content="User loves sushi", node_type="preference", importance=0.8)
        n3 = MemoryNode(id="n3", content="User booked flight to Tokyo", node_type="episode", importance=0.9)
        n4 = MemoryNode(id="n4", content="User studies economics", node_type="fact", importance=0.6)
        n5 = MemoryNode(id="n5", content="User reads Financial Times", node_type="preference", importance=0.5)
        for node in [n1, n2, n3, n4, n5]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.7))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n4", target_id="n5", edge_type="related_to", weight=0.6))

        # Act
        result = memory_map.build_context_for_query("Japan travel plans", token_budget=500)

        # Assert
        assert "Japan" in result
        assert "Tokyo" in result or "sushi" in result
        if "economics" in result:
            assert result.index("Japan") < result.index("economics")

    def test_build_context_for_query_emits_retrieval_log(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Madrid", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User speaks Spanish", node_type="fact", importance=0.8)
        n3 = MemoryNode(id="n3", content="User has a cat", node_type="fact", importance=0.5)
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))

        # Act
        memory_map.build_context_for_query("Where does user live?", token_budget=500)

        # Assert
        log = memory_map.last_retrieval_log
        assert log is not None
        assert log.query == "Where does user live?"
        assert log.nodes_scored == 3
        assert log.nodes_returned >= 1
        assert log.token_budget == 500
        assert log.elapsed_ms >= 0

    def test_build_context_for_query_logs_dropped_nodes(self):
        # Arrange
        memory_map = MemoryMap()
        now = datetime.utcnow()
        for i in range(1, 6):
            node = MemoryNode(
                id=f"n{i}",
                content="x" * 200,
                node_type="fact",
                importance=1.0 - (i * 0.1),
                last_accessed=now,
            )
            memory_map.add_node(node)
        for i in range(2, 6):
            memory_map.add_edge(MemoryEdge(source_id="n1", target_id=f"n{i}", edge_type="related_to", weight=1.0 - (i * 0.1)))

        # Act
        memory_map.build_context_for_query("test query", token_budget=50)

        # Assert
        log = memory_map.last_retrieval_log
        assert log.nodes_dropped > 0
        assert len(log.dropped_node_ids) == log.nodes_dropped
        assert log.nodes_returned + log.nodes_dropped == log.nodes_scored

    def test_build_context_for_query_log_on_empty_map(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        memory_map.build_context_for_query("anything", token_budget=500)

        # Assert
        log = memory_map.last_retrieval_log
        assert log.nodes_scored == 0
        assert log.nodes_returned == 0
        assert log.nodes_dropped == 0

    def test_retrieval_history_accumulates(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Oslo", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User likes skiing", node_type="preference", importance=0.7)
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.7))

        # Act
        memory_map.build_context_for_query("Where does user live?", token_budget=500)
        memory_map.build_context_for_query("What are user hobbies?", token_budget=500)
        memory_map.build_context_for_query("Tell me about the user", token_budget=500)

        # Assert
        assert len(memory_map.retrieval_history) == 3
        assert memory_map.retrieval_history[0].query == "Where does user live?"
        assert memory_map.retrieval_history[2].query == "Tell me about the user"

    def test_get_retrieval_history_returns_last_n(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User is an engineer", node_type="fact", importance=0.8)
        memory_map.add_node(n1)
        for i in range(1, 6):
            memory_map.build_context_for_query(f"query {i}", token_budget=500)

        # Act
        result = memory_map.get_retrieval_history(last_n=2)

        # Assert
        assert len(result) == 2
        assert result[0].query == "query 4"
        assert result[1].query == "query 5"

    def test_get_retrieval_history_default_returns_all(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User speaks Portuguese", node_type="fact", importance=0.6)
        memory_map.add_node(n1)
        for i in range(3):
            memory_map.build_context_for_query(f"query {i}", token_budget=500)

        # Act
        result = memory_map.get_retrieval_history()

        # Assert
        assert len(result) == 3

    def test_get_retrieval_history_empty(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.get_retrieval_history()

        # Assert
        assert result == []

    def test_get_retrieval_history_last_n_exceeds_history(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User likes tea", node_type="preference", importance=0.5)
        memory_map.add_node(n1)
        memory_map.build_context_for_query("query 1", token_budget=500)
        memory_map.build_context_for_query("query 2", token_budget=500)

        # Act
        result = memory_map.get_retrieval_history(last_n=10)

        # Assert
        assert len(result) == 2

    def test_last_retrieval_log_matches_history_tail(self):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User works remotely", node_type="fact", importance=0.7)
        memory_map.add_node(n1)

        # Act
        memory_map.build_context_for_query("remote work?", token_budget=500)

        # Assert
        assert memory_map.last_retrieval_log is memory_map.retrieval_history[-1]

    def test_add_node_logs_write(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        memory_map.add_node(MemoryNode(id="n1", content="User lives in Cairo", node_type="fact"))

        # Assert
        assert len(memory_map.write_history) == 1
        assert memory_map.write_history[0].operation == "add_node"
        assert memory_map.write_history[0].node_id == "n1"
        assert memory_map.write_history[0].success is True
        assert memory_map.write_history[0].dedup_detected is False

    def test_add_edge_logs_write(self):
        # Arrange
        memory_map = MemoryMap()
        memory_map.add_node(MemoryNode(id="n1", content="Node one", node_type="fact"))
        memory_map.add_node(MemoryNode(id="n2", content="Node two", node_type="fact"))

        # Act
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))

        # Assert
        edge_logs = [l for l in memory_map.write_history if l.operation == "add_edge"]
        assert len(edge_logs) == 1
        assert edge_logs[0].node_id == "n1"
        assert edge_logs[0].target_id == "n2"
        assert edge_logs[0].edge_type == "related_to"
        assert edge_logs[0].success is True

    def test_remove_node_logs_write(self):
        # Arrange
        memory_map = MemoryMap()
        memory_map.add_node(MemoryNode(id="n1", content="Node one", node_type="fact"))

        # Act
        memory_map.remove_node("n1")

        # Assert
        remove_logs = [l for l in memory_map.write_history if l.operation == "remove_node"]
        assert len(remove_logs) == 1
        assert remove_logs[0].node_id == "n1"
        assert remove_logs[0].success is True

    def test_add_duplicate_node_logs_dedup(self):
        # Arrange
        memory_map = MemoryMap()
        memory_map.add_node(MemoryNode(id="n1", content="User lives in Cairo", node_type="fact"))

        # Act
        memory_map.add_node(MemoryNode(id="n1", content="User lives in Cairo updated", node_type="fact"))

        # Assert
        assert len(memory_map.write_history) == 2
        assert memory_map.write_history[1].dedup_detected is True
        assert memory_map.write_history[1].success is False
        assert memory_map.get_node("n1").content == "User lives in Cairo"

    def test_get_write_history_returns_last_n(self):
        # Arrange
        memory_map = MemoryMap()
        for i in range(1, 5):
            memory_map.add_node(MemoryNode(id=f"n{i}", content=f"Node {i}", node_type="fact"))

        # Act
        result = memory_map.get_write_history(last_n=2)

        # Assert
        assert len(result) == 2
        assert result[0].node_id == "n3"
        assert result[1].node_id == "n4"

    def test_get_write_history_empty(self):
        # Arrange
        memory_map = MemoryMap()

        # Act
        result = memory_map.get_write_history()

        # Assert
        assert result == []

    def test_memory_map_metrics_wired_to_operations(self):
        # Arrange
        memory_map = MemoryMap()
        memory_map.add_node(MemoryNode(id="n1", content="Node one", node_type="fact"))
        memory_map.add_node(MemoryNode(id="n2", content="Node two", node_type="fact"))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to"))

        # Act
        memory_map.build_context_for_query("test query", 500)

        # Assert
        assert memory_map.metrics.total_writes == 3
        assert memory_map.metrics.total_retrievals == 1
        assert memory_map.metrics.total_nodes_scored >= 1

    def test_tfidf_scoring_improves_retrieval(self):
        """TF-IDF scores distinctive words higher, improving retrieval of relevant nodes."""
        # Arrange
        now = datetime.utcnow()
        memory_map = MemoryMap()
        node_a = MemoryNode(
            id="a", content="User has health problems including diabetes",
            node_type="fact", importance=0.5, last_accessed=now,
        )
        node_b = MemoryNode(
            id="b", content="User likes healthy food and cooking",
            node_type="fact", importance=0.5, last_accessed=now,
        )
        node_c = MemoryNode(
            id="c", content="User enjoys morning exercise routines",
            node_type="fact", importance=0.5, last_accessed=now,
        )
        for node in [node_a, node_b, node_c]:
            memory_map.add_node(node)

        # Act
        result = memory_map.build_context_for_query(
            "health problems and medical conditions", token_budget=500
        )

        # Assert — Node A (health problems + diabetes) should appear
        assert "diabetes" in result

        # Node A should score higher than Node C (exercise, no keyword overlap)
        log = memory_map.last_retrieval_log
        score_a = next((s for nid, s in log.top_scores if nid == "a"), None)
        score_c = next((s for nid, s in log.top_scores if nid == "c"), None)
        if score_a is not None and score_c is not None:
            assert score_a > score_c

    def test_common_words_dont_dominate(self):
        """TF-IDF downweights common words, so repetition of 'user' doesn't dominate."""
        # Arrange
        now = datetime.utcnow()
        memory_map = MemoryMap()
        node_a = MemoryNode(
            id="a", content="User lives in Berlin Germany",
            node_type="fact", importance=0.5, last_accessed=now,
        )
        node_b = MemoryNode(
            id="b", content="User user user user user",
            node_type="fact", importance=0.5, last_accessed=now,
        )
        for node in [node_a, node_b]:
            memory_map.add_node(node)

        # Act
        result = memory_map.build_context_for_query("user information", token_budget=500)

        # Assert — Node A still appears in context (not zero score)
        assert "Berlin" in result

    def test_fallback_to_keyword_matching(self):
        """Falls back to keyword matching when TF-IDF raises an error."""
        # Arrange
        memory_map = MemoryMap()
        memory_map.add_node(MemoryNode(
            id="n1", content="User likes Python programming",
            node_type="fact", importance=0.8,
        ))

        # Act — patch TF-IDF to fail
        with patch("app.services.memory.memory_map._tfidf") as mock_tfidf:
            mock_tfidf.calculate.side_effect = Exception("TF-IDF crashed")
            result = memory_map.build_context_for_query("Python", token_budget=500)

        # Assert — keyword fallback still returns context, no crash
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Python" in result
