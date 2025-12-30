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
