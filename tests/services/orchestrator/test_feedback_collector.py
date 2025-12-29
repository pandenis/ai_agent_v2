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

    def test_add_rating_feedback(self):
        """Test: Add star rating feedback (1-5)."""
        # Arrange
        collector = FeedbackCollector()

        # Act
        collector.add_feedback(
            response_id="resp-456",
            rating=4,
            strategy="enhanced"
        )

        # Assert
        assert len(collector._feedbacks) == 1
        assert collector._feedbacks[0]["rating"] == 4
        assert collector._feedbacks[0]["strategy"] == "enhanced"

    def test_add_feedback_validates_rating_range(self):
        """Test: Rating must be between 1 and 5."""
        # Arrange
        collector = FeedbackCollector()

        # Act & Assert - rating too high
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            collector.add_feedback(
                response_id="resp-789",
                rating=6,
                strategy="direct"
            )

        # Act & Assert - rating too low
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            collector.add_feedback(
                response_id="resp-789",
                rating=0,
                strategy="direct"
            )