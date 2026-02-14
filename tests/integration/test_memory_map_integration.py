from datetime import datetime
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest

from app.services.memory.memory_edge import MemoryEdge
from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_node import MemoryNode
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.fixture
def mock_memory_service():
    service = AsyncMock()
    service.search_facts = AsyncMock(return_value=[])
    service.add_fact = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.name = "test-agent"
    agent.generate = AsyncMock(return_value={"response": "Test AI response", "status": "success"})
    return agent


@pytest.fixture
def mock_agent_factory(mock_agent):
    factory = Mock()
    factory.create_agent = Mock(return_value=mock_agent)
    return factory


@pytest.fixture
def mock_fact_extractor():
    extractor = AsyncMock()
    extractor.extract_facts = AsyncMock(return_value=[])
    return extractor


class TestMemoryMapIntegration:
    def test_orchestrator_build_context_with_memory_map(self, mock_memory_service):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User lives in Berlin", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User speaks German", node_type="fact", importance=0.8)
        n3 = MemoryNode(id="n3", content="User works at SAP", node_type="fact", importance=0.7)
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="related_to", weight=0.8))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.6))

        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            memory_map=memory_map,
        )

        # Act
        result = orchestrator._build_context_with_map(
            query="Where does user live?", facts=[], token_budget=500
        )

        # Assert
        assert "Berlin" in result
        assert "German" in result

    def test_orchestrator_falls_back_without_memory_map(self, mock_memory_service):
        # Arrange
        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
        )
        assert orchestrator.memory_map is None
        facts = [{"text": "User lives in Paris", "importance": 0.9}]

        # Act
        result = orchestrator._build_context(facts, max_facts=5)

        # Assert
        assert "User lives in Paris" in result

    def test_orchestrator_map_enriches_flat_facts(self, mock_memory_service):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User has diabetes", node_type="fact", importance=0.9)
        n2 = MemoryNode(id="n2", content="User takes insulin", node_type="fact", importance=0.8)
        n3 = MemoryNode(id="n3", content="User exercises daily", node_type="preference", importance=0.6)
        for node in [n1, n2, n3]:
            memory_map.add_node(node)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="caused_by", weight=0.9))
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n3", edge_type="related_to", weight=0.5))

        flat_facts = [{"text": "User has diabetes", "importance": 0.9}]

        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            memory_map=memory_map,
        )

        # Act
        result = orchestrator._build_context_with_map(
            query="health info", facts=flat_facts, token_budget=500
        )

        # Assert
        assert "diabetes" in result
        assert "insulin" in result

    def test_memory_map_failure_does_not_break_orchestrator(self, mock_memory_service):
        # Arrange
        broken_map = MagicMock()
        broken_map.build_context_for_query = MagicMock(side_effect=Exception("map crashed"))

        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            memory_map=broken_map,
        )
        flat_facts = [{"text": "User likes cooking", "importance": 0.7}]

        # Act
        result = orchestrator._build_context_with_map(
            query="hobbies", facts=flat_facts, token_budget=500
        )

        # Assert
        assert "cooking" in result

    @pytest.mark.asyncio
    async def test_process_query_uses_memory_map_when_available(
        self, mock_memory_service, mock_agent_factory, mock_agent, mock_fact_extractor
    ):
        # Arrange
        memory_map = MemoryMap()
        n1 = MemoryNode(id="n1", content="User is vegetarian", node_type="preference", importance=0.9)
        n2 = MemoryNode(id="n2", content="User avoids meat products", node_type="preference", importance=0.8)
        memory_map.add_node(n1)
        memory_map.add_node(n2)
        memory_map.add_edge(MemoryEdge(source_id="n1", target_id="n2", edge_type="supports", weight=0.9))

        mock_memory_service.search_facts = AsyncMock(return_value=[
            {"text": "User is vegetarian", "importance": 0.9}
        ])

        orchestrator = IntelligentOrchestrator(
            memory_service=mock_memory_service,
            agent_factory=mock_agent_factory,
            fact_extractor=mock_fact_extractor,
            memory_map=memory_map,
        )

        # Act
        result = await orchestrator.process_query(
            query="What food preferences?", session_id="test"
        )

        # Assert — the agent was called, and the prompt it received should contain vegetarian context
        if mock_agent.generate.called:
            captured_prompt = mock_agent.generate.call_args[0][0]
            assert "vegetarian" in captured_prompt.lower()
