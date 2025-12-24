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
        # Check if too short
        words = query.lower().split()
        if len(words) < 3:
            return AmbiguityResult(
                is_ambiguous=True,
                reason="Query too short to be meaningful"
            )

        for word in words:
            # Remove punctuation
            clean_word = word.strip("?.,!")
            if clean_word in self.AMBIGUOUS_PRONOUNS:
                return AmbiguityResult(
                    is_ambiguous=True,
                    reason=f"Unclear reference: '{clean_word}'"
                )

        return AmbiguityResult(is_ambiguous=False)


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

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple


@dataclass
class AmbiguityResult:
    """Result of ambiguity detection."""
    is_ambiguous: bool
    reason: Optional[str] = None


@dataclass
class ConflictResult:
    """Result of conflict detection."""
    has_conflicts: bool
    conflicts: List[Tuple[Dict, Dict]] = field(default_factory=list)


class EdgeCaseHandler:
    """Handles edge cases in query processing."""

    # Pronouns that need context
    AMBIGUOUS_PRONOUNS = {"it", "this", "that", "they", "them", "he", "she"}

    # Keywords that indicate same topic (for conflict detection)
    CONFLICT_KEYWORDS = {
        "lives in": "location",
        "works at": "job",
        "name is": "name",
        "age is": "age",
        "born in": "birthplace",
    }

    def detect_ambiguity(self, query: str) -> AmbiguityResult:
        """Detect if query is ambiguous."""
        # Check if too short
        words = query.lower().split()
        if len(words) < 3:
            return AmbiguityResult(
                is_ambiguous=True,
                reason="Query too short to be meaningful"
            )

        for word in words:
            # Remove punctuation
            clean_word = word.strip("?.,!")
            if clean_word in self.AMBIGUOUS_PRONOUNS:
                return AmbiguityResult(
                    is_ambiguous=True,
                    reason=f"Unclear reference: '{clean_word}'"
                )

        return AmbiguityResult(is_ambiguous=False)

    def detect_conflicts(self, facts: List[Dict]) -> ConflictResult:
        """Detect conflicting information in facts."""
        conflicts = []

        # Group facts by topic
        topic_facts: Dict[str, List[Dict]] = {}

        for fact in facts:
            text = fact.get("text", "").lower()
            for keyword, topic in self.CONFLICT_KEYWORDS.items():
                if keyword in text:
                    if topic not in topic_facts:
                        topic_facts[topic] = []
                    topic_facts[topic].append(fact)
                    break

        # Find conflicts (multiple facts about same topic)
        for topic, topic_fact_list in topic_facts.items():
            if len(topic_fact_list) > 1:
                # Compare each pair
                for i in range(len(topic_fact_list)):
                    for j in range(i + 1, len(topic_fact_list)):
                        conflicts.append((topic_fact_list[i], topic_fact_list[j]))

        return ConflictResult(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts
        )