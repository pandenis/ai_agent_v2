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
