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