"""
Integration test: _build_context_with_map() wires _infer_subject_hint()
into memory_service.search_facts() (MEM-002-03, step 11 of 13).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.memory_v2 import Fact
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.mark.asyncio
async def test_build_context_passes_subject_hint_to_search_facts():
    """
    Verifies that _build_context_with_map() calls _infer_subject_hint() on
    the query and passes the resulting subject hint as the subject= kwarg
    to memory_service.search_facts(), called exactly once.
    """
    # Arrange
    memory_service = MagicMock()
    memory_service.search_facts = AsyncMock(return_value=[
        Fact(
            fact_id="f1",
            text="FastAPI uses Python asyncio for async handling",
            subject="technology",
            importance=0.8,
        )
    ])

    orchestrator = IntelligentOrchestrator(
        memory_service=memory_service,
        agent_factory=MagicMock(),
    )

    with patch.object(orchestrator, '_infer_subject_hint', return_value='technology'):
        # Act
        await orchestrator._build_context_with_map(
            query="How does FastAPI work?", thread_id="t1"
        )

    # Assert — search_facts called exactly once with subject='technology'
    memory_service.search_facts.assert_called_once()
    call_kwargs = memory_service.search_facts.call_args.kwargs
    assert call_kwargs.get('subject') == 'technology'
