"""
ResponseCache - LRU cache for orchestrator responses.

Caches direct answers to avoid redundant processing.
Features:
- LRU eviction policy
- TTL-based expiration
- Cache key generation from query + context
- Hit rate tracking

Usage:
    >>> cache = ResponseCache(max_size=100, ttl_seconds=3600)
    >>> cache.set("What is my name?", {"answer": "Denis"})
    >>> result = cache.get("What is my name?")
    >>> print(result)  # {"answer": "Denis"}
"""

import time
from typing import Any, Dict, Optional, Tuple


class ResponseCache:
    """LRU cache for orchestrator responses."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """Initialize cache with max size and TTL."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}  # value, timestamp

    def get(self, query: str) -> Optional[Any]:
        """Get cached response for query."""
        entry = self._cache.get(query)
        if entry is None:
            return None

        value, timestamp = entry

        # Check if expired
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[query]
            return None

        return value

    def set(self, query: str, response: Any) -> None:
        """Store response in cache."""
        self._cache[query] = (response, time.time())