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

    def test_separate_limits_per_user(self):
        """Test: Each user has separate rate limit."""
        # Arrange
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Act - user1 hits limit
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        user1_blocked = not limiter.is_allowed("user1")

        # user2 should still be allowed
        user2_allowed = limiter.is_allowed("user2")

        # Assert
        assert user1_blocked is True
        assert user2_allowed is True

    def test_allows_after_window_expires(self):
        """Test: Requests allowed again after window expires."""
        # Arrange
        import time
        limiter = RateLimiter(max_requests=2, window_seconds=0.1)

        # Hit the limit
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False

        # Act - wait for window to expire
        time.sleep(0.15)
        result = limiter.is_allowed("user1")

        # Assert
        assert result is True

    def test_get_stats_for_unknown_user(self):
        """Test: Get stats for unknown user returns zero counts."""
        # Arrange
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # Act
        stats = limiter.get_stats("unknown_user")

        # Assert
        assert stats["requests_count"] == 0
        assert stats["remaining"] == 5

    def test_get_stats_returns_limiter_info(self):
        """Test: Get stats returns rate limiter information."""
        # Arrange
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        limiter.is_allowed("user2")

        # Act
        stats = limiter.get_stats("user1")

        # Assert
        assert stats["requests_count"] == 2
        assert stats["max_requests"] == 5
        assert stats["remaining"] == 3