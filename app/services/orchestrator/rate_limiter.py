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

import time
from typing import Dict, List


class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int = 10, window_seconds: float = 60.0):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key.

        Args:
            key: Identifier (user_id, ip_address, etc.)

        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()

        # Initialize if new key
        if key not in self._requests:
            self._requests[key] = []

        # Remove old requests outside window
        window_start = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        # Check if under limit
        if len(self._requests[key]) >= self.max_requests:
            return False

        # Record this request
        self._requests[key].append(now)
        return True

    def get_stats(self, key: str) -> dict:
        """Get rate limiter statistics for a key."""
        now = time.time()
        window_start = now - self.window_seconds

        # Get current requests in window
        if key not in self._requests:
            requests_count = 0
        else:
            requests_count = len([t for t in self._requests[key] if t > window_start])

        return {
            "requests_count": requests_count,
            "max_requests": self.max_requests,
            "remaining": max(0, self.max_requests - requests_count),
            "window_seconds": self.window_seconds,
        }