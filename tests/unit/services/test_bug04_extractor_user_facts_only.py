"""
BUG-04 regression guard: system prompt must explicitly restrict extraction
to facts about the user and exclude facts about the assistant. Without this,
the model extracts boilerplate assistant sentences as facts.
"""
import pytest
from app.services.fact_extractor import FactExtractor


def test_system_prompt_instructs_user_facts_only():
    """BUG-04 regression guard: system prompt must explicitly
    restrict extraction to facts about the user and exclude facts about
    the assistant. Without this, the model extracts boilerplate assistant
    sentences as facts."""
    extractor = FactExtractor()

    prompt = extractor._get_system_prompt()

    assert "user" in prompt.lower()

    assert any([
        "about the user" in prompt.lower(),
        "about the person" in prompt.lower(),
        "user's facts" in prompt.lower(),
        "only facts about the user" in prompt.lower(),
    ]), "System prompt must explicitly restrict extraction to facts about the user"

    assert any([
        "not about the assistant" in prompt.lower(),
        "ignore assistant" in prompt.lower(),
        "exclude assistant" in prompt.lower(),
        "do not extract facts about yourself" in prompt.lower(),
        "do not extract facts about the assistant" in prompt.lower(),
    ]), "System prompt must explicitly exclude facts about the assistant"
