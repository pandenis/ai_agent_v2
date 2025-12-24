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

    def test_no_conflicts_when_facts_are_compatible(self):
        """Test: No conflicts when facts are about different topics."""
        # Arrange
        handler = EdgeCaseHandler()
        facts = [
            {"text": "User lives in Moscow", "importance": 0.9},
            {"text": "User works at Google", "importance": 0.8},
        ]

        # Act
        result = handler.detect_conflicts(facts)

        # Assert
        assert result.has_conflicts is False
        assert len(result.conflicts) == 0

    def test_handles_empty_memory(self):
        """Test: Detects when memory is empty for a query."""
        # Arrange
        handler = EdgeCaseHandler()
        query = "What is my favorite color?"
        facts = []

        # Act
        result = handler.evaluate_memory_gap(query, facts)

        # Assert
        assert result.has_gap is True
        assert result.suggestion == "web_search"

    def test_no_gap_when_memory_has_relevant_facts(self):
        """Test: No gap when memory contains relevant information."""
        # Arrange
        handler = EdgeCaseHandler()
        query = "What is my favorite color?"
        facts = [
            {"text": "User's favorite color is blue", "importance": 0.9}
        ]

        # Act
        result = handler.evaluate_memory_gap(query, facts)

        # Assert
        assert result.has_gap is False
        assert result.suggestion is None

    def test_timeout_result_creation(self):
        """Test: Can create timeout result with partial data."""
        # Arrange
        handler = EdgeCaseHandler()
        partial_response = "Based on available information..."
        elapsed_time = 15.5  # seconds

        # Act
        result = handler.create_timeout_response(
            partial_response=partial_response,
            elapsed_time=elapsed_time,
            timeout_limit=15.0
        )

        # Assert
        assert result.is_timeout is True
        assert result.partial_response == partial_response
        assert "timeout" in result.message.lower()

    def test_detects_multiple_conflicts(self):
        """Test: Detects all pairs of conflicting facts."""
        # Arrange
        handler = EdgeCaseHandler()
        facts = [
            {"text": "User lives in Moscow", "importance": 0.9},
            {"text": "User lives in Tokyo", "importance": 0.8},
            {"text": "User lives in Paris", "importance": 0.7},
        ]

        # Act
        result = handler.detect_conflicts(facts)

        # Assert
        assert result.has_conflicts is True
        # 3 facts = 3 conflict pairs: (Moscow,Tokyo), (Moscow,Paris), (Tokyo,Paris)
        assert len(result.conflicts) == 3