"""
RateLimiter - Controls request rate to prevent overload.

Features:
- Per-user rate limiting
- Configurable limits (requests per second/minute)
- Token bucket algorithm

Usage:
    >>> limiter = RateLimiter(max_requests=10, window_seconds=60)
    >>> if limiter.is_allowed("user123"):
    ...     process_request()
"""

import pytest
from app.services.orchestrator.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for RateLimiter component."""

    def test_allows_request_under_limit(self):
        """Test: Request is allowed when under rate limit."""
        # Arrange
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # Act
        result = limiter.is_allowed("user123")

        # Assert
        assert result is True