"""Tests for FactExtractor._get_system_prompt() universal extraction prompt (MEM-002-02, step 6 of 13)."""
import re

from app.services.fact_extractor import FactExtractor


def test_system_prompt_allows_any_subject():
    """
    Verifies that the system prompt no longer restricts extraction to user-only facts.
    The new universal prompt must:
    - Not contain the old 'only ... user' restriction pattern
    - Mention 'subject' (the new required field)
    - Contain an Extract instruction
    """
    # Arrange / Act
    prompt = FactExtractor()._get_system_prompt()

    # Assert — old user-only restriction is gone
    assert not re.search(r'\bonly\b.{0,100}\buser\b', prompt, re.IGNORECASE), (
        "Prompt still contains a 'only...user' restriction; universal extraction requires all subjects"
    )

    # Assert — subject field is referenced
    assert "subject" in prompt

    # Assert — extraction instruction is present
    assert re.search(r'\bextract\b', prompt, re.IGNORECASE)


def test_system_prompt_requires_subject_field():
    """
    Verifies that the system prompt requires a 'subject' field in every extracted fact
    and does not list 'assistant' as a valid subject value in the JSON output schema.
    """
    # Arrange / Act
    prompt = FactExtractor()._get_system_prompt()

    # Assert — "subject" appears as a JSON key in the output schema
    assert '"subject"' in prompt

    # Assert — "assistant" is not presented as an allowed subject value in the schema
    assert '"assistant"' not in prompt
