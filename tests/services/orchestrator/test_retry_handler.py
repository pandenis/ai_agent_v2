"""
RetryHandler - Handles retry logic for failed operations.

Features:
- Configurable max retries
- Exponential backoff
- Retry on specific exceptions

Usage:
    >>> handler = RetryHandler(max_retries=3)
    >>> result = handler.execute(some_function)
"""

import pytest
from app.services.orchestrator.retry_handler import RetryHandler


class TestRetryHandler:
    """Tests for RetryHandler component."""

    def test_successful_call_returns_result(self):
        """Test: Successful function call returns result without retry."""
        # Arrange
        handler = RetryHandler(max_retries=3)

        def success_func():
            return "success"

        # Act
        result = handler.execute(success_func)

        # Assert
        assert result == "success"

    def test_retries_on_failure_then_succeeds(self):
        """Test: Retries on failure and succeeds on subsequent attempt."""
        # Arrange
        handler = RetryHandler(max_retries=3, base_delay=0.01)
        call_count = 0

        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"

        # Act
        result = handler.execute(fail_then_succeed)

        # Assert
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries_exceeded(self):
        """Test: Raises exception after all retries exhausted."""
        # Arrange
        handler = RetryHandler(max_retries=2, base_delay=0.01)
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")

        # Act & Assert
        with pytest.raises(ValueError, match="Permanent failure"):
            handler.execute(always_fail)

        # Should have tried 3 times (1 initial + 2 retries)
        assert call_count == 3

    def test_exponential_backoff_delays(self):
        """Test: Uses exponential backoff between retries."""
        # Arrange
        import time
        handler = RetryHandler(max_retries=3, base_delay=0.05, exponential_backoff=True)
        timestamps = []

        def fail_and_record():
            timestamps.append(time.time())
            raise Exception("Failure")

        # Act
        try:
            handler.execute(fail_and_record)
        except Exception:
            pass

        # Assert - check delays increase exponentially
        # Delays should be: 0.05, 0.1, 0.2 (base * 2^attempt)
        assert len(timestamps) == 4  # 1 initial + 3 retries

        delay1 = timestamps[1] - timestamps[0]
        delay2 = timestamps[2] - timestamps[1]
        delay3 = timestamps[3] - timestamps[2]

        # Each delay should be roughly double the previous
        assert delay2 > delay1 * 1.5
        assert delay3 > delay2 * 1.5

    def test_get_stats_returns_retry_info(self):
        """Test: Get stats returns retry information."""
        # Arrange
        handler = RetryHandler(max_retries=3, base_delay=0.01)

        call_count = 0

        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Fail")
            return "success"

        # Act
        handler.execute(fail_twice)
        stats = handler.get_stats()

        # Assert
        assert stats["total_attempts"] == 3
        assert stats["retries_used"] == 2
        assert stats["max_retries"] == 3
        assert stats["success"] is True