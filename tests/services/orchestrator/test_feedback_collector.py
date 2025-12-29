"""
FeedbackCollector - Collects and analyzes user feedback on responses.

Features:
- Thumbs up/down feedback
- Star ratings (1-5)
- Text comments
- Per-strategy analytics
- Quality tracking over time
"""

import pytest
from app.services.orchestrator.feedback_collector import FeedbackCollector


class TestFeedbackCollector:
    """Tests for FeedbackCollector component."""

    def test_feedback_collector_initialization(self):
        """Test: FeedbackCollector initializes correctly."""
        # Arrange & Act
        collector = FeedbackCollector()

        # Assert
        assert collector is not None
        assert hasattr(collector, 'add_feedback')

    def test_add_thumbs_feedback(self):
        """Test: Add thumbs up/down feedback for a response."""
        # Arrange
        collector = FeedbackCollector()

        # Act
        collector.add_feedback(
            response_id="resp-123",
            thumbs_up=True,
            strategy="direct"
        )

        # Assert
        assert len(collector._feedbacks) == 1
        assert collector._feedbacks[0]["response_id"] == "resp-123"
        assert collector._feedbacks[0]["thumbs_up"] == True
        assert collector._feedbacks[0]["strategy"] == "direct"