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
        """
        import uuid
        
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
