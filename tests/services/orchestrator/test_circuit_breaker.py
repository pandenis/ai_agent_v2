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
from app.services.orchestrator.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError


class TestCircuitBreaker:
    """Tests for CircuitBreaker component."""

    def test_initial_state_is_closed(self):
        """Test: Circuit breaker starts in CLOSED state."""
        # Arrange & Act
        breaker = CircuitBreaker(failure_threshold=3)

        # Assert
        assert breaker.state == CircuitState.CLOSED

    def test_successful_call_passes_through(self):
        """Test: Successful function call returns result."""
        # Arrange
        breaker = CircuitBreaker(failure_threshold=3)

        def success_func():
            return "success"

        # Act
        result = breaker.call(success_func)

        # Assert
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_opens_after_failure_threshold(self):
        """Test: Circuit opens after reaching failure threshold."""
        # Arrange
        breaker = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise Exception("Service unavailable")

        # Act - cause 3 failures
        for _ in range(3):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Assert
        assert breaker.state == CircuitState.OPEN

    def test_blocks_calls_when_open(self):
        """Test: Calls are blocked when circuit is open."""
        # Arrange
        breaker = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitState.OPEN

        # Act & Assert - next call should raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            breaker.call(lambda: "should not execute")

    def test_transitions_to_half_open_after_timeout(self):
        """Test: Circuit transitions to HALF_OPEN after recovery timeout."""
        # Arrange
        import time
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        def failing_func():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.state == CircuitState.OPEN

        # Act - wait for recovery timeout
        time.sleep(0.15)

        # Trigger state check
        breaker.check_state()

        # Assert
        assert breaker.state == CircuitState.HALF_OPEN

    def test_closes_after_successful_call_in_half_open(self):
        """Test: Circuit closes after successful call in HALF_OPEN state."""
        # Arrange
        import time
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        def failing_func():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Wait for HALF_OPEN
        time.sleep(0.15)
        breaker.check_state()
        assert breaker.state == CircuitState.HALF_OPEN

        # Act - successful call
        result = breaker.call(lambda: "recovered")

        # Assert
        assert result == "recovered"
        assert breaker.state == CircuitState.CLOSED

    def test_reopens_after_failure_in_half_open(self):
        """Test: Circuit reopens after failure in HALF_OPEN state."""
        # Arrange
        import time
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        def failing_func():
            raise Exception("Service unavailable")

        # Open the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Wait for HALF_OPEN
        time.sleep(0.15)
        breaker.check_state()
        assert breaker.state == CircuitState.HALF_OPEN

        # Act - another failure
        try:
            breaker.call(failing_func)
        except Exception:
            pass

        # Assert - back to OPEN
        assert breaker.state == CircuitState.OPEN

    def test_get_stats_returns_circuit_info(self):
        """Test: Get stats returns circuit breaker information."""
        # Arrange
        breaker = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise Exception("Error")

        # Cause some failures
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Act
        stats = breaker.get_stats()

        # Assert
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 2
        assert stats["failure_threshold"] == 3