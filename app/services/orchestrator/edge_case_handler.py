"""
EdgeCaseHandler - Handles edge cases in query processing.

Handles:
- Ambiguous queries (vague, unclear questions)
- Conflicting information in memory
- Missing memory for queries
- Timeout situations

Usage:
    >>> handler = EdgeCaseHandler()
    >>> result = handler.detect_ambiguity("What about it?")
    >>> print(result.is_ambiguous)  # True
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AmbiguityResult:
    """Result of ambiguity detection."""
    is_ambiguous: bool
    reason: Optional[str] = None


class EdgeCaseHandler:
    """Handles edge cases in query processing."""

    # Pronouns that need context
    AMBIGUOUS_PRONOUNS = {"it", "this", "that", "they", "them", "he", "she"}

    def detect_ambiguity(self, query: str) -> AmbiguityResult:
        """Detect if query is ambiguous."""
        words = query.lower().split()

        for word in words:
            # Remove punctuation
            clean_word = word.strip("?.,!")
            if clean_word in self.AMBIGUOUS_PRONOUNS:
                return AmbiguityResult(
                    is_ambiguous=True,
                    reason=f"Unclear reference: '{clean_word}'"
                )

        return AmbiguityResult(is_ambiguous=False)