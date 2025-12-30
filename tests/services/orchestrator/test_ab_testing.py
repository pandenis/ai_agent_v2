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
