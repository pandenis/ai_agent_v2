"""
A/B Testing Framework for Intelligent Orchestrator

Enables running experiments to compare different strategies:
- Create experiments with multiple variants
- Deterministic user assignment (same user → same variant)
- Track success rates and response times
- Determine winning variants
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class ExperimentResult:
    """Single result from an experiment"""
    experiment_id: str
    variant: str
    user_id: str
    success: bool
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Experiment:
    """A/B Test Experiment configuration"""
    experiment_id: str
    name: str
    variants: List[str]
    traffic_split: List[float]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


class ABTestingService:
    """
    Manages A/B testing experiments.
    """

    def __init__(self):
        """Initialize the A/B testing service"""
        self.experiments: Dict[str, Experiment] = {}
        self.results: List[ExperimentResult] = []

    def create_experiment(
        self,
        name: str,
        variants: List[str],
        traffic_split: List[float]
    ) -> str:
        """Create a new A/B experiment."""
        # Validate
        total = sum(traffic_split)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        if len(variants) != len(traffic_split):
            raise ValueError("Variants and traffic_split must have same length")

        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"

        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            variants=variants,
            traffic_split=traffic_split
        )
        self.experiments[experiment_id] = experiment
        return experiment_id

    def get_variant(
        self,
        experiment_id: str,
        user_id: str
    ) -> str:
        """Get variant for a user (deterministic assignment)."""
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if not experiment.is_active:
            raise ValueError(f"Experiment {experiment_id} is not active")

        # Create deterministic hash from experiment + user
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()

        # Convert hash to float between 0 and 1
        hash_float = int(hash_value[:8], 16) / 0xFFFFFFFF

        # Determine variant based on traffic split
        cumulative = 0.0
        for i, split in enumerate(experiment.traffic_split):
            cumulative += split
            if hash_float < cumulative:
                return experiment.variants[i]

        # Fallback to last variant
        return experiment.variants[-1]

    def record_result(
        self,
        experiment_id: str,
        variant: str,
        user_id: str,
        success: bool,
        latency_ms: float
    ) -> bool:
        """Record a result for an experiment."""
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            return False

        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            user_id=user_id,
            success=success,
            latency_ms=latency_ms
        )

        self.results.append(result)
        return True

    def get_experiment_stats(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """Get statistics for an experiment."""
        experiment = self.experiments.get(experiment_id)

        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Filter results for this experiment
        exp_results = [r for r in self.results if r.experiment_id == experiment_id]

        # Group results by variant
        variant_results: Dict[str, List[ExperimentResult]] = {
            v: [] for v in experiment.variants
        }

        for result in exp_results:
            if result.variant in variant_results:
                variant_results[result.variant].append(result)

        # Calculate stats per variant
        variant_stats = {}
        for variant, results in variant_results.items():
            if results:
                success_count = sum(1 for r in results if r.success)
                total_latency = sum(r.latency_ms for r in results)

                variant_stats[variant] = {
                    "trials": len(results),
                    "successes": success_count,
                    "success_rate": success_count / len(results),
                    "avg_latency_ms": total_latency / len(results)
                }
            else:
                variant_stats[variant] = {
                    "trials": 0,
                    "successes": 0,
                    "success_rate": 0.0,
                    "avg_latency_ms": 0.0
                }

        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "total_trials": len(exp_results),  # ← total_trials
            "variants": variant_stats
        }

    def is_statistically_significant(
        self,
        experiment_id: str,
        min_samples: int = 30
    ) -> Dict[str, Any]:
        """Check if experiment results are statistically significant."""
        stats = self.get_experiment_stats(experiment_id)

        variant_data = stats["variants"]

        # Check if enough samples
        for variant, data in variant_data.items():
            if data["trials"] < min_samples:
                return {
                    "is_significant": False,
                    "reason": "insufficient_data",
                    "min_samples_required": min_samples
                }

        # Find best and worst variants
        success_rates = [
            (v, d["success_rate"])
            for v, d in variant_data.items()
            if d["trials"] > 0
        ]

        if len(success_rates) < 2:
            return {
                "is_significant": False,
                "reason": "no_significant_difference",
            }

        success_rates.sort(key=lambda x: x[1], reverse=True)
        best_variant, best_rate = success_rates[0]
        worst_variant, worst_rate = success_rates[-1]

        # Simple significance check: >10% difference
        difference = best_rate - worst_rate

        if difference < 0.10:
            return {
                "is_significant": False,
                "reason": "no_significant_difference",
                "rate_difference": difference,
            }

        return {
            "is_significant": True,
            "best_variant": best_variant,
            "best_success_rate": best_rate,
            "rate_difference": difference,
            "confidence": 0.95 if difference > 0.20 else 0.90
        }

    def get_winner(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Determine the winning variant based on success rate."""
        try:
            stats = self.get_experiment_stats(experiment_id)
        except ValueError:
            return None

        if not stats["variants"]:
            return None

        best_variant = None
        best_rate = -1.0
        worst_rate = 1.1

        for variant, data in stats["variants"].items():
            if data["count"] > 0:
                if data["success_rate"] > best_rate:
                    best_rate = data["success_rate"]
                    best_variant = variant
                if data["success_rate"] < worst_rate:
                    worst_rate = data["success_rate"]

        if best_variant is None:
            return None

        improvement = 0.0
        if worst_rate > 0:
            improvement = (best_rate - worst_rate) / worst_rate

        return {
            "variant": best_variant,
            "success_rate": best_rate,
            "improvement": improvement
        }

    def deactivate_experiment(self, experiment_id: str) -> bool:
        """Deactivate an experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False
        experiment.is_active = False
        return True

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments with their status."""
        return [
            {
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "variants": exp.variants,
                "is_active": exp.is_active,
                "total_results": len([r for r in self.results if r.experiment_id == exp.experiment_id]),
                "created_at": exp.created_at.isoformat()
            }
            for exp in self.experiments.values()
        ]


# Aliases
ABTestingManager = ABTestingService