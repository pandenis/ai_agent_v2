"""
Tests for A/B Testing Service.

A/B Testing enables experimentation with different strategies
(direct, enhanced, deep_reasoning) to find optimal approach
for different query types.

Test categories:
- Experiment configuration
- Traffic splitting
- Results collection
- Statistical analysis
"""

import pytest
from app.services.orchestrator.ab_testing import Experiment


class TestExperiment:
    """Tests for Experiment dataclass."""

    def test_experiment_creation(self):
        """Test: Experiment can be created with basic fields."""
        # Arrange & Act
        experiment = Experiment(
            experiment_id="exp_001",
            name="Strategy Comparison",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Assert
        assert experiment.experiment_id == "exp_001"
        assert experiment.name == "Strategy Comparison"
        assert experiment.variants == ["direct", "enhanced"]
        assert experiment.traffic_split == [0.5, 0.5]


class TestExperimentResult:
    """Tests for ExperimentResult dataclass."""

    def test_experiment_result_creation(self):
        """Test: ExperimentResult stores single trial outcome."""
        # Arrange & Act
        from app.services.orchestrator.ab_testing import ExperimentResult

        result = ExperimentResult(
            experiment_id="exp_001",
            variant="direct",
            user_id="user_123",
            success=True,
            latency_ms=150.5
        )

        # Assert
        assert result.experiment_id == "exp_001"
        assert result.variant == "direct"
        assert result.user_id == "user_123"
        assert result.success is True
        assert result.latency_ms == 150.5


class TestABTestingService:
    """Tests for ABTestingService."""

    def test_service_creation(self):
        """Test: ABTestingService can be instantiated."""
        # Arrange & Act
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()

        # Assert
        assert service is not None
        assert service.experiments == {}
        assert service.results == []

    def test_create_experiment(self):
        """Test: Create experiment with variants and traffic split."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()

        # Act
        exp_id = service.create_experiment(
            name="Strategy Comparison",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Assert
        assert exp_id is not None
        assert exp_id.startswith("exp_")
        assert exp_id in service.experiments
        assert service.experiments[exp_id].name == "Strategy Comparison"
        assert service.experiments[exp_id].variants == ["direct", "enhanced"]

    def test_get_variant_returns_valid_variant(self):
        """Test: get_variant returns one of the defined variants."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Test Experiment",
            variants=["direct", "enhanced", "deep_reasoning"],
            traffic_split=[0.5, 0.3, 0.2]
        )

        # Act
        variant = service.get_variant(exp_id, user_id="user_123")

        # Assert
        assert variant in ["direct", "enhanced", "deep_reasoning"]

    def test_get_variant_consistent_for_same_user(self):
        """Test: Same user always gets the same variant."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Consistency Test",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Act - call multiple times for same user
        variant1 = service.get_variant(exp_id, user_id="user_456")
        variant2 = service.get_variant(exp_id, user_id="user_456")
        variant3 = service.get_variant(exp_id, user_id="user_456")

        # Assert - should always be the same
        assert variant1 == variant2 == variant3

    def test_get_variant_consistent_for_same_user(self):
        """Test: Same user always gets the same variant."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Consistency Test",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Act - call multiple times for same user
        variant1 = service.get_variant(exp_id, user_id="user_456")
        variant2 = service.get_variant(exp_id, user_id="user_456")
        variant3 = service.get_variant(exp_id, user_id="user_456")

        # Assert - should always be the same
        assert variant1 == variant2 == variant3

    def test_record_result(self):
        """Test: Record experiment result for a user."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Record Test",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Act
        service.record_result(
            experiment_id=exp_id,
            variant="direct",
            user_id="user_789",
            success=True,
            latency_ms=120.5
        )

        # Assert
        assert len(service.results) == 1
        assert service.results[0].experiment_id == exp_id
        assert service.results[0].variant == "direct"
        assert service.results[0].success is True
        assert service.results[0].latency_ms == 120.5

    def test_get_experiment_stats(self):
        """Test: Get aggregated statistics for an experiment."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Stats Test",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Record some results
        service.record_result(exp_id, "direct", "user_1", success=True, latency_ms=100)
        service.record_result(exp_id, "direct", "user_2", success=True, latency_ms=150)
        service.record_result(exp_id, "direct", "user_3", success=False, latency_ms=200)
        service.record_result(exp_id, "enhanced", "user_4", success=True, latency_ms=300)
        service.record_result(exp_id, "enhanced", "user_5", success=False, latency_ms=350)

        # Act
        stats = service.get_experiment_stats(exp_id)

        # Assert
        assert stats["experiment_id"] == exp_id
        assert stats["total_trials"] == 5
        assert "variants" in stats
        
        # Check direct variant stats
        assert stats["variants"]["direct"]["trials"] == 3
        assert stats["variants"]["direct"]["successes"] == 2
        assert stats["variants"]["direct"]["success_rate"] == pytest.approx(0.667, rel=0.01)
        assert stats["variants"]["direct"]["avg_latency_ms"] == pytest.approx(150.0)
        
        # Check enhanced variant stats
        assert stats["variants"]["enhanced"]["trials"] == 2
        assert stats["variants"]["enhanced"]["successes"] == 1
        assert stats["variants"]["enhanced"]["success_rate"] == pytest.approx(0.5)

    def test_is_statistically_significant_not_enough_data(self):
        """Test: Returns False when not enough data for significance."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Significance Test",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Only 2 results - not enough data
        service.record_result(exp_id, "direct", "user_1", success=True, latency_ms=100)
        service.record_result(exp_id, "enhanced", "user_2", success=False, latency_ms=200)

        # Act
        result = service.is_statistically_significant(exp_id)

        # Assert
        assert result["is_significant"] is False
        assert result["reason"] == "insufficient_data"

    def test_is_statistically_significant_with_clear_winner(self):
        """Test: Returns True when there's a clear winner with enough data."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()
        exp_id = service.create_experiment(
            name="Clear Winner Test",
            variants=["direct", "enhanced"],
            traffic_split=[0.5, 0.5]
        )

        # Add 30+ results per variant with clear difference
        # Direct: 90% success rate (27/30)
        for i in range(27):
            service.record_result(exp_id, "direct", f"user_d_{i}", success=True, latency_ms=100)
        for i in range(3):
            service.record_result(exp_id, "direct", f"user_d_fail_{i}", success=False, latency_ms=100)

        # Enhanced: 60% success rate (18/30)
        for i in range(18):
            service.record_result(exp_id, "enhanced", f"user_e_{i}", success=True, latency_ms=200)
        for i in range(12):
            service.record_result(exp_id, "enhanced", f"user_e_fail_{i}", success=False, latency_ms=200)

        # Act
        result = service.is_statistically_significant(exp_id)

        # Assert
        assert result["is_significant"] is True
        assert result["best_variant"] == "direct"
        assert result["rate_difference"] == pytest.approx(0.3, rel=0.01)

    def test_get_variant_experiment_not_found(self):
        """Test: get_variant raises error for unknown experiment."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            service.get_variant("nonexistent_exp", user_id="user_1")

    def test_get_variant_experiment_not_found(self):
        """Test: get_variant raises error for unknown experiment."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            service.get_variant("nonexistent_exp", user_id="user_1")

    def test_create_experiment_validates_traffic_split(self):
        """Test: create_experiment validates traffic_split sums to 1.0."""
        # Arrange
        from app.services.orchestrator.ab_testing import ABTestingService

        service = ABTestingService()

        # Act & Assert - traffic split doesn't sum to 1.0
        with pytest.raises(ValueError, match="sum to 1.0"):
            service.create_experiment(
                name="Invalid Split",
                variants=["a", "b"],
                traffic_split=[0.3, 0.3]  # Sums to 0.6, not 1.0
            )
