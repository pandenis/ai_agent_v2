"""
ResponseCache - Caches orchestrator responses to avoid redundant AI calls.

This component stores responses in memory with TTL (Time To Live) to:
1. Speed up repeated queries (100ms vs 3s)
2. Reduce API costs (free vs $0.0003)
3. Improve user experience

Cache Key: hash(query + session_id)
TTL: 3600 seconds (1 hour)
Storage: In-memory dict (production: Redis)

Usage:
    >>> cache = ResponseCache()
    >>> cache.set(query, session_id, response)
    >>> result = cache.get(query, session_id)
"""
import hashlib
import time
from typing import Optional, Dict, Any


class ResponseCache:
    """In-memory cache for orchestrator responses"""

    def __init__(self, ttl: int = 3600):
        """
        Initialize cache

        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self._cache: Dict[str, tuple[Any, float]] = {}

    def _generate_key(self, query: str, session_id: str) -> str:
        """Generate cache key from query and session"""
        combined = f"{query}:{session_id}"
        return hashlib.md5(combined.encode()).hexdigest()

    def set(self, query: str, session_id: str, response: Any) -> None:
        """Store response in cache"""
        key = self._generate_key(query, session_id)
        timestamp = time.time()
        self._cache[key] = (response, timestamp)

    def get(self, query: str, session_id: str) -> Optional[Any]:
        """Retrieve response from cache"""
        key = self._generate_key(query, session_id)

        if key not in self._cache:
            return None

        response, timestamp = self._cache[key]

        # Check TTL
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None

        return response