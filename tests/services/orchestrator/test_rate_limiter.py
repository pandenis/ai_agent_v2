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

    def test_blocks_request_over_limit(self):
        """Test: Request is blocked when over rate limit."""
        # Arrange
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Act - make 3 allowed requests
        for _ in range(3):
            limiter.is_allowed("user123")

        # 4th request should be blocked
        result = limiter.is_allowed("user123")

        # Assert
        assert result is False