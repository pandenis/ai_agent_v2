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

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple


class ResponseCache:
    """LRU cache for orchestrator responses."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """Initialize cache with max size and TTL."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._query_to_key: Dict[str, str] = {}  # Maps original query to cache key

    def _generate_key(self, query: str, context: Optional[Dict] = None) -> str:
        """Generate cache key from query and context."""
        key_data = query
        if context:
            key_data += json.dumps(context, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, context: Optional[Dict] = None) -> Optional[Any]:
        """Get cached response for query."""
        key = self._generate_key(query, context)
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        value, timestamp = entry

        # Check if expired
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1

        return value

    def set(self, query: str, response: Any, context: Optional[Dict] = None) -> None:
        """Store response in cache."""
        key = self._generate_key(query, context)

        # If key exists, remove it first (will be re-added at end)
        if key in self._cache:
            del self._cache[key]

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # Remove oldest (first item)

        self._cache[key] = (response, time.time())
        self._query_to_key[query] = key

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "max_size": self.max_size,
        }

    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all cache entries where query starts with prefix.

        Args:
            prefix: Query prefix to match

        Returns:
            Number of entries removed
        """
        keys_to_remove = []
        queries_to_remove = []

        for query, key in self._query_to_key.items():
            if query.startswith(prefix):
                keys_to_remove.append(key)
                queries_to_remove.append(query)

        for key in keys_to_remove:
            if key in self._cache:
                del self._cache[key]

        for query in queries_to_remove:
            del self._query_to_key[query]

        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cached entries and reset stats."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0