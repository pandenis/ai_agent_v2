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

    def test_cache_returns_none_for_missing_key(self):
        """Test: Cache returns None for non-existent key."""
        # Arrange
        cache = ResponseCache()

        # Act
        result = cache.get("unknown query")

        # Assert
        assert result is None

    def test_cache_expires_after_ttl(self):
        """Test: Cache entry expires after TTL seconds."""
        # Arrange
        cache = ResponseCache(ttl_seconds=1)  # 1 second TTL
        query = "What is the weather?"
        response = {"answer": "Sunny"}

        # Act
        cache.set(query, response)

        # Simulate time passing
        import time
        time.sleep(1.1)  # Wait slightly more than TTL

        result = cache.get(query)

        # Assert
        assert result is None  # Should be expired