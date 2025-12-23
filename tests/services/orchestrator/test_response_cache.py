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

import pytest
from app.services.orchestrator.response_cache import ResponseCache


class TestResponseCache:
    """Tests for ResponseCache component."""

    def test_cache_stores_and_retrieves_value(self):
        """Test: Cache can store and retrieve a value."""
        # Arrange
        cache = ResponseCache()
        query = "What is my name?"
        response = {"answer": "Denis", "strategy": "direct"}

        # Act
        cache.set(query, response)
        result = cache.get(query)

        # Assert
        assert result == response