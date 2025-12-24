"""
EdgeCaseHandler - Handles edge cases in query processing.

Handles:
- Ambiguous queries (vague, unclear questions)
- Conflicting information in memory
- Missing memory for queries
- Timeout situations

Usage:
    >>> handler = EdgeCaseHandler()
    >>> result = handler.detect_ambiguity("it")
    >>> print(result.is_ambiguous)  # True
"""

import pytest
from app.services.orchestrator.edge_case_handler import EdgeCaseHandler


class TestEdgeCaseHandler:
    """Tests for EdgeCaseHandler component."""

    def test_detects_ambiguous_pronoun_query(self):
        """Test: Detects query with unclear pronoun reference."""
        # Arrange
        handler = EdgeCaseHandler()
        query = "What about it?"

        # Act
        result = handler.detect_ambiguity(query)

        # Assert
        assert result.is_ambiguous is True
        assert "it" in result.reason.lower()

    def test_detects_too_short_query(self):
        """Test: Detects query that is too short to be meaningful."""
        # Arrange
        handler = EdgeCaseHandler()
        query = "How?"

        # Act
        result = handler.detect_ambiguity(query)

        # Assert
        assert result.is_ambiguous is True
        assert "short" in result.reason.lower()

    def test_clear_query_not_ambiguous(self):
        """Test: Clear query is not flagged as ambiguous."""
        # Arrange
        handler = EdgeCaseHandler()
        query = "What is the weather in Tokyo?"

        # Act
        result = handler.detect_ambiguity(query)

        # Assert
        assert result.is_ambiguous is False
        assert result.reason is None

    def test_detects_conflicting_facts(self):
        """Test: Detects conflicting information in memory facts."""
        # Arrange
        handler = EdgeCaseHandler()
        facts = [
            {"text": "User lives in Moscow", "importance": 0.9},
            {"text": "User lives in Tokyo", "importance": 0.8},
        ]

        # Act
        result = handler.detect_conflicts(facts)

        # Assert
        assert result.has_conflicts is True
        assert len(result.conflicts) >= 1