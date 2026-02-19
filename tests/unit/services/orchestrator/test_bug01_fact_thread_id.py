"""
BUG-01 regression guard: add_fact must be called with thread_id=session_id.
Without this, all facts are stored with thread_id=NULL and memory_coverage
is always 0.0.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.memory_v2 import Fact
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.mark.asyncio
async def test_add_fact_called_with_thread_id():
    """BUG-01 regression guard: add_fact must be called with
    thread_id=session_id. Without this, all facts are stored with
    thread_id=NULL and memory_coverage is always 0.0."""
    memory_service = AsyncMock()
    agent_factory = MagicMock()
    fact_extractor = AsyncMock()

    fake_fact = Fact(fact_id="f1", text="User lives in Ramat Gan")
    fact_extractor.extract_facts.return_value = [fake_fact]

    orchestrator = IntelligentOrchestrator(
        memory_service=memory_service,
        agent_factory=agent_factory,
        fact_extractor=fact_extractor,
    )

    session_id = "test-session-xyz"

    await orchestrator._extract_and_save_facts(
        session_id=session_id,
        query="I live in Ramat Gan",
        response="Got it, noted.",
    )

    memory_service.add_fact.assert_called_once()
    call_args = memory_service.add_fact.call_args
    assert call_args.kwargs.get("thread_id") == session_id
