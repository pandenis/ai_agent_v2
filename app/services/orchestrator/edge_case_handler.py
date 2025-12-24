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


@dataclass
class MemoryGapResult:
    """Result of memory gap evaluation."""
    has_gap: bool
    suggestion: Optional[str] = None  # "web_search", "ask_user", None


@dataclass
class TimeoutResult:
    """Result when operation times out."""
    is_timeout: bool
    partial_response: Optional[str] = None
    message: str = ""
    elapsed_time: float = 0.0


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

    def evaluate_memory_gap(self, query: str, facts: List[Dict]) -> MemoryGapResult:
        """Evaluate if there's a memory gap for the query."""
        if not facts:
            return MemoryGapResult(
                has_gap=True,
                suggestion="web_search"
            )

        return MemoryGapResult(has_gap=False)

    def create_timeout_response(
        self,
        partial_response: Optional[str],
        elapsed_time: float,
        timeout_limit: float
    ) -> TimeoutResult:
        """Create a timeout response with partial data."""
        return TimeoutResult(
            is_timeout=True,
            partial_response=partial_response,
            message=f"Operation timeout after {elapsed_time:.1f}s (limit: {timeout_limit:.1f}s)",
            elapsed_time=elapsed_time
        )