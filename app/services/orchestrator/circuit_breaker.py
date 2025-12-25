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

import time
from enum import Enum
from typing import Callable, Any, Optional


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal, requests pass through
    OPEN = "open"          # Blocked, too many failures
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitOpenError(Exception):
    """Raised when circuit is open and calls are blocked."""
    pass


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
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None

    def check_state(self) -> None:
        """Check and update circuit state based on timeout."""
        if self.state == CircuitState.OPEN and self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN

    def call(self, func: Callable[[], Any]) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call

        Returns:
            Result of function call

        Raises:
            CircuitOpenError: If circuit is open
        """
        self.check_state()

        if self.state == CircuitState.OPEN:
            raise CircuitOpenError("Circuit is open, call blocked")

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> None:
        """Handle successful call."""
        self._failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN