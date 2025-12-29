"""
FeedbackCollector - Collects and analyzes user feedback on responses.

Features:
- Thumbs up/down feedback
- Star ratings (1-5)
- Text comments
- Per-strategy analytics
- Quality tracking over time

Usage:
    >>> collector = FeedbackCollector()
    >>> collector.add_feedback(response_id="123", rating=5, strategy="direct")
    >>> stats = collector.get_stats()
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class FeedbackCollector:
    """Collects and analyzes user feedback on responses."""

    def __init__(self):
        """Initialize feedback collector."""
        self._feedbacks: List[Dict[str, Any]] = []

    def add_feedback(
            self,
            response_id: str,
            strategy: str,
            thumbs_up: Optional[bool] = None,
            rating: Optional[int] = None,
            comment: Optional[str] = None
    ) -> None:
        """
        Add feedback for a response.

        Args:
            response_id: Unique identifier for the response
            strategy: Strategy used (direct, enhanced, deep_reasoning)
            thumbs_up: True for positive, False for negative
            rating: Star rating 1-5
            comment: Optional text feedback
        """
        # Validate rating range
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")

        feedback = {
            "response_id": response_id,
            "strategy": strategy,
            "thumbs_up": thumbs_up,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.now()
        }
        self._feedbacks.append(feedback)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Returns:
            Dictionary with feedback metrics
        """
        thumbs_up_count = sum(1 for f in self._feedbacks if f.get("thumbs_up") is True)
        thumbs_down_count = sum(1 for f in self._feedbacks if f.get("thumbs_up") is False)

        # Calculate per-strategy stats
        by_strategy: Dict[str, Dict[str, int]] = {}
        for feedback in self._feedbacks:
            strategy = feedback["strategy"]
            if strategy not in by_strategy:
                by_strategy[strategy] = {"count": 0, "thumbs_up": 0, "thumbs_down": 0}

            by_strategy[strategy]["count"] += 1
            if feedback.get("thumbs_up") is True:
                by_strategy[strategy]["thumbs_up"] += 1
            elif feedback.get("thumbs_up") is False:
                by_strategy[strategy]["thumbs_down"] += 1

        return {
            "total_feedbacks": len(self._feedbacks),
            "thumbs_up_count": thumbs_up_count,
            "thumbs_down_count": thumbs_down_count,
            "by_strategy": by_strategy,
        }