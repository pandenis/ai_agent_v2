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
from typing import List, Dict, Any


class RelevanceScorer:
    """Calculate relevance scores for memory retrieval"""

    # Scoring weights
    WEIGHT_SIMILARITY = 0.5
    WEIGHT_RECENCY = 0.2
    WEIGHT_IMPORTANCE = 0.3

    MEMORY_ACCESS_TIERS = {
        "direct": {"min_score": 0.7, "fact_types": ["static"]},
        "enhanced": {"min_score": 0.5, "fact_types": ["static", "derived", "temporal"]},
        "deep_reasoning": {"min_score": 0.3, "fact_types": ["static", "derived", "temporal"]},
    }

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
        days_old = (datetime.utcnow() - created_at).days

        if days_old <= 0:
            return 1.0
        if days_old >= max_days:
            return 0.0

        return 1.0 - (days_old / max_days)

    def calculate_relevance(
        self,
        query: str,
        fact_text: str,
        created_at: datetime,
        importance: float
    ) -> float:
        """Calculate combined relevance score.

        Formula: 0.5 * similarity + 0.2 * recency + 0.3 * importance

        Args:
            query: Search query string
            fact_text: Fact text to score
            created_at: When the fact was created
            importance: Pre-assigned importance (0.0-1.0)

        Returns:
            Combined relevance score (0.0-1.0)
        """
        similarity = self.text_similarity(query, fact_text)
        recency = self.recency_score(created_at)

        return (
            self.WEIGHT_SIMILARITY * similarity +
            self.WEIGHT_RECENCY * recency +
            self.WEIGHT_IMPORTANCE * importance
        )

    def score_facts(
        self,
        query: str,
        facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score and sort facts by relevance.

        Args:
            query: Search query string
            facts: List of fact dicts with 'text', 'created_at', 'importance'

        Returns:
            Facts with 'relevance_score' added, sorted descending
        """
        scored_facts = []

        for fact in facts:
            relevance = self.calculate_relevance(
                query=query,
                fact_text=fact["text"],
                created_at=fact["created_at"],
                importance=fact["importance"]
            )
            scored_fact = {**fact, "relevance_score": relevance}
            scored_facts.append(scored_fact)

        # Sort by relevance descending
        scored_facts.sort(key=lambda f: f["relevance_score"], reverse=True)

        return scored_facts

    def score_and_filter(
        self,
        query: str,
        facts: List[Dict[str, Any]],
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Score, filter, and sort facts by relevance.

        Args:
            query: Search query string
            facts: List of fact dicts with 'text', 'created_at', 'importance'
            min_score: Minimum relevance score threshold (0.0-1.0)

        Returns:
            Facts above min_score with 'relevance_score' added, sorted descending
        """
        scored_facts = self.score_facts(query, facts)

        # Filter by min_score
        filtered_facts = [f for f in scored_facts if f["relevance_score"] >= min_score]

        return filtered_facts

    def get_memory_access(self, strategy: str) -> Dict[str, Any]:
        """Get memory access rules for a strategy tier.

        Args:
            strategy: One of 'direct', 'enhanced', 'deep_reasoning'

        Returns:
            Dict with 'min_score' and 'fact_types' keys
        """
        return self.MEMORY_ACCESS_TIERS.get(
            strategy,
            self.MEMORY_ACCESS_TIERS["enhanced"]  # Default fallback
        )

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text.

        Uses approximation: tokens ≈ words * 1.3

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count (rounded)
        """
        word_count = len(text.split())
        return round(word_count * 1.3)