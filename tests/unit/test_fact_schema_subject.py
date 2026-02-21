"""Tests for Fact dataclass subject field (MEM-002-01, step 1 of 13)."""
from app.models.memory_v2 import Fact


def test_fact_schema_has_subject_field():
    """
    Verifies that the Fact dataclass has a 'subject' field with a default
    value of 'user', and that it accepts an explicit string value.
    """
    # Arrange / Act — default subject
    fact_default = Fact(fact_id="f1", text="User lives in Paris")

    # Assert — default value
    assert fact_default.subject == "user"

    # Arrange / Act — explicit subject
    fact_explicit = Fact(fact_id="f2", text="Python is a language", subject="technology")

    # Assert — explicit value
    assert fact_explicit.subject == "technology"
