"""
BUG-03 regression guard: extract_facts must be called with
messages=[{'role':'user','content':query}] and context={'session_id':...}.
Calling with conversation_text= silently swallows all facts.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.mark.asyncio
async def test_extract_facts_called_with_correct_signature():
    """BUG-03 regression guard: extract_facts must be called with
    messages=[{'role':'user','content':query}] and context={'session_id':...}.
    Calling with conversation_text= silently swallows all facts."""
    memory_service = AsyncMock()
    fact_extractor = AsyncMock()
    fact_extractor.extract_facts.return_value = []

    orchestrator = IntelligentOrchestrator(
        memory_service=memory_service,
        agent_factory=MagicMock(),
        fact_extractor=fact_extractor,
    )

    session_id = "test-session-abc"
    query = "I live in Ramat Gan and I love hiking"

    await orchestrator._extract_and_save_facts(
        session_id=session_id,
        query=query,
        response="some response",
    )

    fact_extractor.extract_facts.assert_called_once()
    call_kwargs = fact_extractor.extract_facts.call_args.kwargs
    assert "messages" in call_kwargs
    assert call_kwargs["messages"] == [{"role": "user", "content": query}]
    assert "conversation_text" not in call_kwargs
    assert call_kwargs.get("context", {}).get("session_id") == session_id
