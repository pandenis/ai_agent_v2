"""
A/B Testing Service for Strategy Experimentation.

Enables controlled experiments to compare different response
strategies (direct, enhanced, deep_reasoning) and find optimal
approach for different query types.

Features:
- Experiment configuration with variants
- Traffic splitting by percentage
- Results collection and aggregation
- Statistical significance analysis

Usage:
    >>> service = ABTestingService()
    >>> exp_id = service.create_experiment(
    ...     name="Strategy Test",
    ...     variants=["direct", "enhanced"],
    ...     traffic_split=[0.5, 0.5]
    ... )
    >>> variant = service.get_variant(exp_id, user_id="user_123")
    >>> service.record_result(exp_id, variant, success=True, latency_ms=150)
    >>> stats = service.get_experiment_stats(exp_id)
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Experiment:
    """Configuration for an A/B test experiment."""
    
    experiment_id: str
    name: str
    variants: List[str]
    traffic_split: List[float]


@dataclass
class ExperimentResult:
    """Result of a single experiment trial."""
    
    experiment_id: str
    variant: str
    user_id: str
    success: bool
    latency_ms: float


class ABTestingService:
    """Service for managing A/B testing experiments."""
    
    def __init__(self):
        """Initialize A/B testing service."""
        self.experiments: dict = {}
        self.results: list = []

    def create_experiment(
        self,
        name: str,
        variants: List[str],
        traffic_split: List[float]
    ) -> str:
        """Create a new A/B test experiment.
        
        Args:
            name: Human-readable experiment name
            variants: List of variant names (e.g., ["direct", "enhanced"])
            traffic_split: Traffic percentage for each variant (must sum to 1.0)
            
        Returns:
            Experiment ID
            
        Raises:
            ValueError: If traffic_split doesn't sum to 1.0 or lengths don't match
        """
        import uuid
        
        # Validate traffic split sums to 1.0
        if abs(sum(traffic_split) - 1.0) > 0.001:
            raise ValueError(f"traffic_split must sum to 1.0, got {sum(traffic_split)}")
        
        # Validate lengths match
        if len(variants) != len(traffic_split):
            raise ValueError(f"variants and traffic_split must have same length")
        
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        experiment = Experiment(
            experiment_id=exp_id,
            name=name,
            variants=variants,
            traffic_split=traffic_split
        )
        
        self.experiments[exp_id] = experiment
        
        return exp_id

    def get_variant(self, experiment_id: str, user_id: str) -> str:
        """Get variant for a user in an experiment.
        
        Uses consistent hashing based on user_id to ensure
        the same user always gets the same variant.
        
        Args:
            experiment_id: ID of the experiment
            user_id: Unique user identifier
            
        Returns:
            Selected variant name
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Consistent hash based on user_id + experiment_id
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = hash(hash_input) % 1000 / 1000.0  # 0.0 to 0.999
        
        # Select variant based on traffic split
        cumulative = 0.0
        for variant, split in zip(experiment.variants, experiment.traffic_split):
            cumulative += split
            if hash_value < cumulative:
                return variant
        
        # Fallback to last variant
        return experiment.variants[-1]

    def record_result(
        self,
        experiment_id: str,
        variant: str,
        user_id: str,
        success: bool,
        latency_ms: float
    ) -> None:
        """Record the result of an experiment trial.
        
        Args:
            experiment_id: ID of the experiment
            variant: Variant that was used
            user_id: Unique user identifier
            success: Whether the trial was successful
            latency_ms: Response latency in milliseconds
        """
        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            user_id=user_id,
            success=success,
            latency_ms=latency_ms
        )
        
        self.results.append(result)

    def get_experiment_stats(self, experiment_id: str) -> dict:
        """Get aggregated statistics for an experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            Dictionary with experiment statistics
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Filter results for this experiment
        exp_results = [r for r in self.results if r.experiment_id == experiment_id]
        
        # Aggregate by variant
        variants_stats = {}
        for variant in experiment.variants:
            variant_results = [r for r in exp_results if r.variant == variant]
            trials = len(variant_results)
            
            if trials > 0:
                successes = sum(1 for r in variant_results if r.success)
                total_latency = sum(r.latency_ms for r in variant_results)
                
                variants_stats[variant] = {
                    "trials": trials,
                    "successes": successes,
                    "success_rate": successes / trials,
                    "avg_latency_ms": total_latency / trials
                }
            else:
                variants_stats[variant] = {
                    "trials": 0,
                    "successes": 0,
                    "success_rate": 0.0,
                    "avg_latency_ms": 0.0
                }
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "total_trials": len(exp_results),
            "variants": variants_stats
        }

    def is_statistically_significant(
        self,
        experiment_id: str,
        min_samples_per_variant: int = 30,
        confidence_level: float = 0.95
    ) -> dict:
        """Check if experiment results are statistically significant.
        
        Uses a simple approach: requires minimum samples per variant
        and checks if success rate difference exceeds threshold.
        
        Args:
            experiment_id: ID of the experiment
            min_samples_per_variant: Minimum trials per variant (default: 30)
            confidence_level: Required confidence level (default: 0.95)
            
        Returns:
            Dictionary with significance analysis
        """
        stats = self.get_experiment_stats(experiment_id)
        variants_stats = stats["variants"]
        
        # Check minimum samples
        for variant, data in variants_stats.items():
            if data["trials"] < min_samples_per_variant:
                return {
                    "is_significant": False,
                    "reason": "insufficient_data",
                    "min_required": min_samples_per_variant,
                    "current_trials": {v: d["trials"] for v, d in variants_stats.items()}
                }
        
        # Get success rates
        success_rates = {v: d["success_rate"] for v, d in variants_stats.items()}
        
        # Find best and worst variants
        best_variant = max(success_rates, key=success_rates.get)
        worst_variant = min(success_rates, key=success_rates.get)
        
        rate_difference = success_rates[best_variant] - success_rates[worst_variant]
        
        # Simple significance threshold based on confidence level
        # For 95% confidence, require at least 10% difference
        threshold = 0.10 if confidence_level >= 0.95 else 0.05
        
        is_significant = rate_difference >= threshold
        
        return {
            "is_significant": is_significant,
            "reason": "significant_difference" if is_significant else "no_significant_difference",
            "best_variant": best_variant,
            "worst_variant": worst_variant,
            "rate_difference": rate_difference,
            "threshold": threshold,
            "success_rates": success_rates
        }
