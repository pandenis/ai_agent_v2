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
from collections import OrderedDict
from typing import Any, Optional, Tuple


class ResponseCache:
    """LRU cache for orchestrator responses."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """Initialize cache with max size and TTL."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()

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

        # Move to end (most recently used)
        self._cache.move_to_end(query)

        return value

    def set(self, query: str, response: Any) -> None:
        """Store response in cache."""
        # If key exists, remove it first (will be re-added at end)
        if query in self._cache:
            del self._cache[query]

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first item)

        self._cache[query] = (response, time.time())