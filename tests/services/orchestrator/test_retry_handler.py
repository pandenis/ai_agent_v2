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