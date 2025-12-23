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

    def test_cache_evicts_oldest_when_full(self):
        """Test: Cache evicts least recently used entry when max size exceeded."""
        # Arrange
        cache = ResponseCache(max_size=2, ttl_seconds=3600)

        # Act - fill cache beyond capacity
        cache.set("query1", {"answer": "first"})
        cache.set("query2", {"answer": "second"})
        cache.set("query3", {"answer": "third"})  # Should evict query1

        # Assert
        assert cache.get("query1") is None  # Evicted
        assert cache.get("query2") == {"answer": "second"}
        assert cache.get("query3") == {"answer": "third"}

    def test_cache_tracks_hit_rate(self):
        """Test: Cache tracks hits and misses for statistics."""
        # Arrange
        cache = ResponseCache()
        cache.set("query1", {"answer": "first"})

        # Act
        cache.get("query1")  # Hit
        cache.get("query1")  # Hit
        cache.get("unknown")  # Miss
        cache.get("missing")  # Miss

        # Assert
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5  # 50%