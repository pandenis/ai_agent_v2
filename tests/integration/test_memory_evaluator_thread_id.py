"""
Integration test: MemoryEvaluator passes thread_id to search_facts()
so that session-scoped facts are actually found (MEM-002-05 bug fix).

Without the fix, search_facts() is called with thread_id=None, which only
matches facts with a NULL thread_id — never the session-scoped facts stored
by the orchestrator.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.memory_v2 import Fact
from app.services.orchestrator.memory_evaluator import MemoryEvaluator


@pytest.mark.asyncio
async def test_evaluator_passes_thread_id_to_search_facts():
    """
    Verifies that MemoryEvaluator.evaluate() forwards thread_id to
    memory_service.search_facts() so that session-scoped facts stored
    under that thread_id are included in coverage evaluation.

    Regression: previously search_facts() was called with thread_id=None,
    causing memory_coverage to always be 0.0 and the 'direct' strategy to
    never fire for well-covered sessions.
    """
    # Arrange
    memory_service = MagicMock()
    memory_service.search_facts = AsyncMock(return_value=[
        Fact(
            fact_id=f"f{i}",
            text="My name is Denis",
            subject="user",
            importance=0.9,
            thread_id="session-abc",
        )
        for i in range(3)
    ])

    evaluator = MemoryEvaluator(memory_service=memory_service)

    query_analysis = MagicMock()
    query_analysis.topics = ["name"]
    query_analysis.entities = []

    # Act
    await evaluator.evaluate(
        query_analysis=query_analysis,
        thread_id="session-abc",
        subject_hint="user",
    )

    # Assert — search_facts called with thread_id="session-abc"
    memory_service.search_facts.assert_called_once()
    call_kwargs = memory_service.search_facts.call_args.kwargs
    assert call_kwargs.get("thread_id") == "session-abc", (
        f"Expected thread_id='session-abc' in search_facts kwargs, got: {call_kwargs}"
    )
    assert call_kwargs.get("thread_id") is not None, (
        "search_facts must not be called with thread_id=None — "
        "that only matches global (NULL-thread) facts, not session facts"
    )
