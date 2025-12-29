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

    def test_get_stats_returns_basic_metrics(self):
        """Test: get_stats returns basic feedback metrics."""
        # Arrange
        collector = FeedbackCollector()
        collector.add_feedback(response_id="r1", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r2", strategy="direct", thumbs_up=False)
        collector.add_feedback(response_id="r3", strategy="enhanced", thumbs_up=True)

        # Act
        stats = collector.get_stats()

        # Assert
        assert stats["total_feedbacks"] == 3
        assert stats["thumbs_up_count"] == 2
        assert stats["thumbs_down_count"] == 1

    def test_get_stats_per_strategy(self):
        """Test: get_stats includes metrics per strategy."""
        # Arrange
        collector = FeedbackCollector()
        collector.add_feedback(response_id="r1", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r2", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r3", strategy="enhanced", thumbs_up=False)
        collector.add_feedback(response_id="r4", strategy="deep_reasoning", rating=5)

        # Act
        stats = collector.get_stats()

        # Assert
        assert "by_strategy" in stats
        assert stats["by_strategy"]["direct"]["count"] == 2
        assert stats["by_strategy"]["direct"]["thumbs_up"] == 2
        assert stats["by_strategy"]["enhanced"]["count"] == 1
        assert stats["by_strategy"]["enhanced"]["thumbs_down"] == 1
        assert stats["by_strategy"]["deep_reasoning"]["count"] == 1

    def test_get_stats_includes_average_rating(self):
        """Test: get_stats includes average rating overall and per strategy."""
        # Arrange
        collector = FeedbackCollector()
        collector.add_feedback(response_id="r1", strategy="direct", rating=5)
        collector.add_feedback(response_id="r2", strategy="direct", rating=4)
        collector.add_feedback(response_id="r3", strategy="enhanced", rating=3)
        collector.add_feedback(response_id="r4", strategy="enhanced", rating=5)

        # Act
        stats = collector.get_stats()

        # Assert
        assert stats["average_rating"] == 4.25  # (5+4+3+5) / 4
        assert stats["by_strategy"]["direct"]["average_rating"] == 4.5  # (5+4) / 2
        assert stats["by_strategy"]["enhanced"]["average_rating"] == 4.0  # (3+5) / 2

    def test_get_stats_includes_satisfaction_rate(self):
        """Test: get_stats includes satisfaction rate (positive / total)."""
        # Arrange
        collector = FeedbackCollector()
        collector.add_feedback(response_id="r1", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r2", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r3", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r4", strategy="enhanced", thumbs_up=False)

        # Act
        stats = collector.get_stats()

        # Assert
        assert stats["satisfaction_rate"] == 0.75  # 3 positive / 4 total

    def test_get_best_strategy(self):
        """Test: get_best_strategy returns strategy with highest satisfaction."""
        # Arrange
        collector = FeedbackCollector()
        # Direct: 1/2 = 50% satisfaction
        collector.add_feedback(response_id="r1", strategy="direct", thumbs_up=True)
        collector.add_feedback(response_id="r2", strategy="direct", thumbs_up=False)
        # Enhanced: 3/3 = 100% satisfaction
        collector.add_feedback(response_id="r3", strategy="enhanced", thumbs_up=True)
        collector.add_feedback(response_id="r4", strategy="enhanced", thumbs_up=True)
        collector.add_feedback(response_id="r5", strategy="enhanced", thumbs_up=True)
        # Deep reasoning: 2/3 = 67% satisfaction
        collector.add_feedback(response_id="r6", strategy="deep_reasoning", thumbs_up=True)
        collector.add_feedback(response_id="r7", strategy="deep_reasoning", thumbs_up=True)
        collector.add_feedback(response_id="r8", strategy="deep_reasoning", thumbs_up=False)

        # Act
        best = collector.get_best_strategy()

        # Assert
        assert best["strategy"] == "enhanced"
        assert best["satisfaction_rate"] == 1.0