"""
BUG-02 regression guard: extract_facts must receive user query only,
not the full User+Assistant exchange. Assistant responses contain
boilerplate that pollutes the fact store with facts about the assistant
instead of facts about the user.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator.orchestrator import IntelligentOrchestrator


@pytest.mark.asyncio
async def test_extract_facts_called_with_user_query_only():
    """BUG-02 regression guard: extract_facts must receive user query only."""
    memory_service = AsyncMock()
    fact_extractor = AsyncMock()
    fact_extractor.extract_facts.return_value = []

    orchestrator = IntelligentOrchestrator(
        memory_service=memory_service,
        agent_factory=MagicMock(),
        fact_extractor=fact_extractor,
    )

    await orchestrator._extract_and_save_facts(
        session_id="test-session-abc",
        query="I live in Ramat Gan and I love hiking",
        response="Assistant is a language model and is ready to help.",
    )

    fact_extractor.extract_facts.assert_called_once()
    call_kwargs = fact_extractor.extract_facts.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert "Assistant" not in user_content
    assert "Ramat Gan" in user_content
