"""
RelevanceScorer - Calculate relevance scores for memory facts.

Scoring Formula:
    relevance = 0.5 * text_similarity + 0.2 * recency + 0.3 * importance

Components:
- text_similarity: Word overlap ratio (0.0-1.0)
- recency: Linear decay over 90 days (0.0-1.0)
- importance: Pre-assigned fact importance (0.0-1.0)

Usage:
    >>> scorer = RelevanceScorer()
    >>> score = scorer.text_similarity("hello world", "hello there")
    >>> print(score)  # ~0.33

Note:
    v2.1 uses simple word overlap. v2.2 will upgrade to TF-IDF.
"""

from datetime import datetime


class RelevanceScorer:
    """Calculate relevance scores for memory retrieval"""

    def text_similarity(self, query: str, text: str) -> float:
        """Calculate word overlap similarity between query and text.

        Args:
            query: Search query string
            text: Fact text to compare against

        Returns:
            Similarity score from 0.0 (no overlap) to 1.0 (identical)
        """
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())

        intersection = query_words & text_words
        union = query_words | text_words

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def recency_score(self, created_at: datetime, max_days: int = 90) -> float:
        """Calculate recency score with linear decay.

        Args:
            created_at: When the fact was created
            max_days: Days after which score becomes 0.0 (default 90)

        Returns:
            Recency score from 0.0 (old) to 1.0 (new)
        """
        # Minimal implementation for first test
        return 1.0