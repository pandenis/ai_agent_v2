"""Tests for Fact dataclass subject field (MEM-002-01, steps 1-3 of 13)."""
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


def test_fact_model_to_dataclass_includes_subject():
    """
    Verifies that FactModel.to_dataclass() correctly maps the 'subject'
    column onto the resulting Fact dataclass instance.
    """
    # Arrange
    model = FactModel(
        fact_id="f3", text="Metformin treats T2D",
        thread_id="t1", importance=0.8, subject='medical'
    )

    # Act
    fact = model.to_dataclass()

    # Assert
    assert fact.subject == 'medical'
