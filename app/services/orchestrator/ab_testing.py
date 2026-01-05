"""
A/B Testing Framework for Intelligent Orchestrator

Enables running experiments to compare different strategies:
- Create experiments with multiple variants
- Deterministic user assignment (same user → same variant)
- Track success rates and response times
- Determine winning variants

Usage:
    manager = ABTestingManager()

    # Create experiment
    manager.create_experiment(
        name="strategy_test",
        variants=["direct", "enhanced"],
        traffic_split=[0.5, 0.5]
    )

    # Get variant for user
    variant = manager.get_variant("strategy_test", user_id="user123")

    # Record result
    manager.record_result(
        experiment_name="strategy_test",
        variant=variant,
        user_id="user123",
        success=True,
        response_time_ms=150.0
    )

    # Get winner
    winner = manager.get_winner("strategy_test")
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class ExperimentResult:
    """Single result from an experiment"""
    user_id: str
    variant: str
    success: bool
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Experiment:
    """A/B Test Experiment configuration"""
    name: str
    variants: List[str]
    traffic_split: List[float]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    results: List[ExperimentResult] = field(default_factory=list)

    def __post_init__(self):
        """Validate traffic split sums to 1.0"""
        total = sum(self.traffic_split)
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        if len(self.variants) != len(self.traffic_split):
            raise ValueError("Number of variants must match traffic split length")


class ABTestingManager:
    """
    Manages A/B testing experiments.

    Features:
    - Deterministic variant assignment (hash-based)
    - Traffic splitting with configurable ratios
    - Result tracking and statistics
    - Winner determination
    """

    def __init__(self):
        """Initialize the A/B testing manager"""
        self._experiments: Dict[str, Experiment] = {}

    def create_experiment(
        self,
        name: str,
        variants: List[str],
        traffic_split: List[float]
    ) -> Experiment:
        """
        Create a new A/B experiment.

        Args:
            name: Unique experiment name
            variants: List of variant names (e.g., ["control", "treatment"])
            traffic_split: Traffic allocation per variant (must sum to 1.0)

        Returns:
            Created Experiment object

        Example:
            >>> manager.create_experiment(
            ...     name="button_color",
            ...     variants=["red", "blue", "green"],
            ...     traffic_split=[0.33, 0.33, 0.34]
            ... )
        """
        experiment = Experiment(
            name=name,
            variants=variants,
            traffic_split=traffic_split
        )
        self._experiments[name] = experiment
        return experiment

    def get_variant(
        self,
        experiment_name: str,
        user_id: str
    ) -> Optional[str]:
        """
        Get variant for a user (deterministic assignment).

        Same user_id will always get the same variant for a given experiment.
        Uses hash-based assignment for consistent distribution.

        Args:
            experiment_name: Name of the experiment
            user_id: Unique user identifier

        Returns:
            Variant name or None if experiment doesn't exist/inactive
        """
        experiment = self._experiments.get(experiment_name)

        if not experiment or not experiment.is_active:
            return None

        # Create deterministic hash from experiment + user
        hash_input = f"{experiment_name}:{user_id}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()

        # Convert hash to float between 0 and 1
        hash_float = int(hash_value[:8], 16) / 0xFFFFFFFF

        # Determine variant based on traffic split
        cumulative = 0.0
        for i, split in enumerate(experiment.traffic_split):
            cumulative += split
            if hash_float < cumulative:
                return experiment.variants[i]

        # Fallback to last variant (shouldn't happen with valid split)
        return experiment.variants[-1]

    def record_result(
        self,
        experiment_name: str,
        variant: str,
        user_id: str,
        success: bool,
        response_time_ms: float
    ) -> bool:
        """
        Record a result for an experiment.

        Args:
            experiment_name: Name of the experiment
            variant: Which variant was used
            user_id: User identifier
            success: Whether the interaction was successful
            response_time_ms: Response time in milliseconds

        Returns:
            True if recorded successfully, False otherwise
        """
        experiment = self._experiments.get(experiment_name)

        if not experiment:
            return False

        result = ExperimentResult(
            user_id=user_id,
            variant=variant,
            success=success,
            response_time_ms=response_time_ms
        )

        experiment.results.append(result)
        return True

    def get_experiment_stats(
        self,
        experiment_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for an experiment.

        Returns:
            Dictionary with stats per variant:
            {
                "total_participants": 100,
                "variants": {
                    "control": {
                        "count": 50,
                        "success_rate": 0.7,
                        "avg_response_time_ms": 200.0
                    },
                    "treatment": {
                        "count": 50,
                        "success_rate": 0.85,
                        "avg_response_time_ms": 150.0
                    }
                }
            }
        """
        experiment = self._experiments.get(experiment_name)

        if not experiment:
            return None

        # Group results by variant
        variant_results: Dict[str, List[ExperimentResult]] = {
            v: [] for v in experiment.variants
        }

        for result in experiment.results:
            if result.variant in variant_results:
                variant_results[result.variant].append(result)

        # Calculate stats per variant
        variant_stats = {}
        for variant, results in variant_results.items():
            if results:
                success_count = sum(1 for r in results if r.success)
                total_time = sum(r.response_time_ms for r in results)

                variant_stats[variant] = {
                    "count": len(results),
                    "success_rate": success_count / len(results),
                    "avg_response_time_ms": total_time / len(results)
                }
            else:
                variant_stats[variant] = {
                    "count": 0,
                    "success_rate": 0.0,
                    "avg_response_time_ms": 0.0
                }

        return {
            "total_participants": len(experiment.results),
            "variants": variant_stats
        }

    def get_winner(
        self,
        experiment_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Determine the winning variant based on success rate.

        Returns:
            Dictionary with winner info:
            {
                "variant": "treatment",
                "success_rate": 0.85,
                "improvement": 0.21  # 21% improvement over worst
            }
        """
        stats = self.get_experiment_stats(experiment_name)

        if not stats or not stats["variants"]:
            return None

        # Find variant with highest success rate
        best_variant = None
        best_rate = -1.0
        worst_rate = 1.1

        for variant, data in stats["variants"].items():
            if data["count"] > 0:  # Only consider variants with data
                if data["success_rate"] > best_rate:
                    best_rate = data["success_rate"]
                    best_variant = variant
                if data["success_rate"] < worst_rate:
                    worst_rate = data["success_rate"]

        if best_variant is None:
            return None

        # Calculate improvement over baseline (worst variant)
        improvement = 0.0
        if worst_rate > 0:
            improvement = (best_rate - worst_rate) / worst_rate

        return {
            "variant": best_variant,
            "success_rate": best_rate,
            "improvement": improvement
        }

    def deactivate_experiment(self, experiment_name: str) -> bool:
        """
        Deactivate an experiment.

        Deactivated experiments no longer assign variants to users.

        Args:
            experiment_name: Name of the experiment to deactivate

        Returns:
            True if deactivated, False if experiment not found
        """
        experiment = self._experiments.get(experiment_name)

        if not experiment:
            return False

        experiment.is_active = False
        return True

    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        List all experiments with their status.

        Returns:
            List of experiment summaries
        """
        return [
            {
                "name": exp.name,
                "variants": exp.variants,
                "is_active": exp.is_active,
                "total_results": len(exp.results),
                "created_at": exp.created_at.isoformat()
            }
            for exp in self._experiments.values()
        ]

ABTestingService = ABTestingManager
