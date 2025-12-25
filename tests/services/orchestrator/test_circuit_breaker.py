"""
CircuitBreaker - Prevents cascade failures in distributed systems.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests blocked
- HALF_OPEN: Testing if service recovered

Usage:
    >>> breaker = CircuitBreaker(failure_threshold=3)
    >>> breaker.call(some_function)
"""

import pytest
from app.services.orchestrator.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Tests for CircuitBreaker component."""

    def test_initial_state_is_closed(self):
        """Test: Circuit breaker starts in CLOSED state."""
        # Arrange & Act
        breaker = CircuitBreaker(failure_threshold=3)

        # Assert
        assert breaker.state == CircuitState.CLOSED