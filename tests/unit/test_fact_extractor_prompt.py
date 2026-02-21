"""Tests for FactExtractor._get_system_prompt() universal extraction prompt (MEM-002-02, steps 6-7 of 13)."""
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


def test_parse_extraction_maps_subject():
    """
    Verifies that _parse_extraction_result() correctly maps the 'subject'
    field from the JSON dict onto each returned Fact object.
    """
    # Arrange
    raw = {
        "facts": [
            {
                "text": "FastAPI uses Python asyncio for async handling",
                "importance": 0.75,
                "confidence": 0.9,
                "fact_type": "technical_explanation",
                "tags": ["fastapi", "async", "python"],
                "subject": "technology"
            },
            {
                "text": "User prefers dark mode",
                "importance": 0.8,
                "confidence": 0.95,
                "fact_type": "preference",
                "tags": ["ui", "preference"],
                "subject": "user"
            }
        ]
    }

    # Act
    result = FactExtractor()._parse_extraction_result(raw)

    # Assert
    assert len(result) == 2
    assert result[0].subject == 'technology'
    assert result[1].subject == 'user'
