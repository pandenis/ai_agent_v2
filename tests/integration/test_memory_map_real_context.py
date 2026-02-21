"""
INT-05: MemoryMap graph-enriched context with real nodes.

Gap covered: all existing MemoryMap tests mock MemoryService or MemoryMap.
This test uses a real MemoryMap instance with real nodes to verify
_build_context_with_map returns non-empty enriched context.
"""
from unittest.mock import MagicMock

import pytest

from app.services.memory.memory_map import MemoryMap
from app.services.memory.memory_node import MemoryNode
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.mark.asyncio
async def test_build_context_with_map_returns_enriched_context_from_real_nodes():
    """Verify _build_context_with_map produces non-empty context from a real
    MemoryMap with real nodes. All existing tests mock one or both components —
    this test exercises the real graph path."""
    memory_map = MemoryMap()
    memory_map.add_node(MemoryNode(id="user_city", content="User lives in Paris", node_type="fact", importance=0.9))
    memory_map.add_node(MemoryNode(id="user_hobby", content="User enjoys cycling", node_type="fact", importance=0.8))

    orchestrator = IntelligentOrchestrator(
        memory_service=MagicMock(),
        agent_factory=MagicMock(),
        fact_extractor=MagicMock(),
        memory_map=memory_map,
    )

    facts = [
        {"text": "User lives in Paris", "importance": 0.9, "confidence": 0.9},
        {"text": "User enjoys cycling", "importance": 0.8, "confidence": 0.8},
    ]

    result = await orchestrator._build_context_with_map(
        query="Tell me about the user",
        facts=facts,
        token_budget=500,
    )

    assert result is not None
    assert len(result) > 0
    assert "Paris" in result or "cycling" in result
