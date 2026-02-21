"""Tests for IntelligentOrchestrator._infer_subject_hint() (MEM-002-03, step 10 of 13)."""
from unittest.mock import MagicMock

from app.services.orchestrator.orchestrator import IntelligentOrchestrator


def _make_orchestrator():
    """Minimal orchestrator instance with all services mocked."""
    return IntelligentOrchestrator(
        memory_service=MagicMock(),
        agent_factory=MagicMock(),
    )


def test_infer_subject_hint_personal_query():
    """
    Verifies that a query containing a personal keyword ('my') causes
    _infer_subject_hint() to return 'user'.
    """
    # Arrange
    orchestrator = _make_orchestrator()
    query = "What is my name?"

    # Act
    result = orchestrator._infer_subject_hint(query)

    # Assert
    assert result == 'user'


def test_infer_subject_hint_technology_query():
    """
    Verifies that a query containing a technology keyword ('async', 'FastAPI')
    causes _infer_subject_hint() to return 'technology'.
    """
    # Arrange
    orchestrator = _make_orchestrator()
    query = "How does FastAPI handle async requests?"

    # Act
    result = orchestrator._infer_subject_hint(query)

    # Assert
    assert result == 'technology'


def test_infer_subject_hint_medical_query():
    """
    Verifies that a query containing a medical keyword ('dose') causes
    _infer_subject_hint() to return 'medical'.
    """
    # Arrange
    orchestrator = _make_orchestrator()
    query = "What is the recommended dose for metformin?"

    # Act
    result = orchestrator._infer_subject_hint(query)

    # Assert
    assert result == 'medical'


def test_infer_subject_hint_personal_takes_priority():
    """
    Verifies that personal keywords take precedence over medical keywords.
    'My doctor prescribed me metformin' contains 'my ' (personal) AND 'metformin'
    — but personal keywords are checked first, so the result is 'user'.
    """
    # Arrange
    orchestrator = _make_orchestrator()
    query = "My doctor prescribed me metformin"

    # Act
    result = orchestrator._infer_subject_hint(query)

    # Assert
    assert result == 'user'


def test_infer_subject_hint_unknown_returns_none():
    """
    Verifies that a query matching none of the keyword lists causes
    _infer_subject_hint() to return None.
    """
    # Arrange
    orchestrator = _make_orchestrator()
    query = "Tell me about the history of Rome"

    # Act
    result = orchestrator._infer_subject_hint(query)

    # Assert
    assert result is None
