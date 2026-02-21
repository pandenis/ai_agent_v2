"""Tests for Fact dataclass subject field (MEM-002-01, steps 1-2 of 13)."""
from app.models.memory_v2 import Fact, FactModel


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


def test_fact_model_subject_persists():
    """
    Verifies that FactModel has a 'subject' column whose server_default
    of 'user' is reflected when the model is instantiated without an
    explicit subject value.
    """
    # Arrange / Act
    model = FactModel(fact_id="f2", text="FastAPI is async", thread_id="t1", importance=0.7)

    # Assert
    assert model.subject == 'user'
