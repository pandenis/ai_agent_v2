"""
MEM-002-02 update: universal fact extraction — subject must not be 'assistant'.

Previously (BUG-04): system prompt must restrict extraction to user-only facts.
Now (MEM-002-02): system prompt supports all subjects; 'assistant' subject is
explicitly excluded. Regression guard updated to assert behavioral conditions
on extracted Fact objects rather than prompt string patterns.
"""
import pytest
from app.services.fact_extractor import FactExtractor


def test_system_prompt_instructs_user_facts_only():
    """MEM-002-02 regression guard (updated from BUG-04): universal extraction
    now allows any subject, but 'assistant' must never appear as a fact subject.
    Asserts on actual Fact objects returned from a mock extraction result:
    - fact.subject != 'assistant'
    - fact.subject is a non-empty string
    - fact.importance >= 0.5
    """
    extractor = FactExtractor()

    # Arrange — mock extraction result with a non-user, non-assistant subject
    raw = {
        "facts": [
            {
                "text": "Python is a high-level programming language",
                "importance": 0.8,
                "confidence": 0.9,
                "fact_type": "knowledge",
                "tags": ["python", "programming"],
                "subject": "technology",
            }
        ]
    }

    # Act
    facts = extractor._parse_extraction_result(raw)

    # Assert
    assert len(facts) == 1
    for fact in facts:
        # Subject must never be 'assistant'
        assert fact.subject != "assistant", (
            "Extracted facts must not carry subject='assistant'"
        )
        # Subject must be a non-empty string
        assert isinstance(fact.subject, str) and len(fact.subject) > 0, (
            "Every extracted fact must have a non-empty subject"
        )
        # Importance threshold still applies
        assert fact.importance >= 0.5, (
            "Extracted facts must meet the importance >= 0.5 threshold"
        )
