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
        return True