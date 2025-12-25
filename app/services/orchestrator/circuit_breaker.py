"""
CircuitBreaker - Prevents cascade failures in distributed systems.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests blocked
- HALF_OPEN: Testing if service recovered

Usage:
    >>> breaker = CircuitBreaker(failure_threshold=3)
    >>> result = breaker.call(some_function)
"""

from enum import Enum
from typing import Callable, Any


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal, requests pass through
    OPEN = "open"  # Blocked, too many failures
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED