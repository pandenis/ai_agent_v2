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

    def test_cache_differentiates_by_context(self):
        """Test: Same query with different context stored separately."""
        # Arrange
        cache = ResponseCache()
        query = "What should I eat?"
        context1 = {"user_preference": "vegetarian"}
        context2 = {"user_preference": "meat_lover"}

        # Act
        cache.set(query, {"answer": "Salad"}, context=context1)
        cache.set(query, {"answer": "Steak"}, context=context2)

        # Assert
        result1 = cache.get(query, context=context1)
        result2 = cache.get(query, context=context2)

        assert result1 == {"answer": "Salad"}
        assert result2 == {"answer": "Steak"}

    def test_cache_clear_removes_all_entries(self):
        """Test: Clear removes all cached entries and resets stats."""
        # Arrange
        cache = ResponseCache()
        cache.set("query1", {"answer": "first"})
        cache.set("query2", {"answer": "second"})
        cache.get("query1")  # Create a hit

        # Act
        cache.clear()

        # Assert - check stats FIRST (before get calls add misses)
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

        # Now verify entries are gone
        assert cache.get("query1") is None
        assert cache.get("query2") is None

    def test_cache_stats_when_empty(self):
        """Test: Stats return zero hit rate when no operations performed."""
        # Arrange
        cache = ResponseCache()

        # Act
        stats = cache.get_stats()

        # Assert
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["size"] == 0

    def test_cache_updates_existing_key(self):
        """Test: Setting same key updates value and moves to most recent."""
        # Arrange
        cache = ResponseCache(max_size=2)
        cache.set("query1", {"answer": "old"})
        cache.set("query2", {"answer": "second"})

        # Act - update query1 (should move it to end)
        cache.set("query1", {"answer": "new"})

        # Add third item - should evict query2 (oldest), not query1
        cache.set("query3", {"answer": "third"})

        # Assert
        assert cache.get("query1") == {"answer": "new"}
        assert cache.get("query2") is None  # Evicted
        assert cache.get("query3") == {"answer": "third"}

    def test_invalidate_by_prefix(self):
        """Test: Invalidate all entries matching a prefix."""
        # Arrange
        cache = ResponseCache()
        cache.set("weather:london", {"temp": "15C"})
        cache.set("weather:paris", {"temp": "18C"})
        cache.set("news:tech", {"headline": "AI news"})
        cache.set("news:sports", {"headline": "Football"})

        # Act - invalidate all weather queries
        removed_count = cache.invalidate_by_prefix("weather:")

        # Assert
        assert removed_count == 2
        assert cache.get("weather:london") is None
        assert cache.get("weather:paris") is None
        assert cache.get("news:tech") == {"headline": "AI news"}
        assert cache.get("news:sports") == {"headline": "Football"}

    def test_get_stats_includes_estimated_bytes(self):
        """Test: Stats include estimated memory usage in bytes."""
        # Arrange
        cache = ResponseCache()
        cache.set("query1", {"answer": "short"})
        cache.set("query2", {"answer": "a much longer response text here"})

        # Act
        stats = cache.get_stats()

        # Assert
        assert "estimated_bytes" in stats
        assert stats["estimated_bytes"] > 0

    def test_cache_with_strategy_tag(self):
        """Test: Cache entries can be tagged with strategy for selective retrieval."""
        # Arrange
        cache = ResponseCache()

        # Act - set with strategy tags
        cache.set("query1", {"answer": "direct"}, strategy="direct")
        cache.set("query2", {"answer": "enhanced"}, strategy="enhanced")
        cache.set("query3", {"answer": "deep"}, strategy="deep_reasoning")

        # Assert - all retrievable
        assert cache.get("query1") == {"answer": "direct"}
        assert cache.get("query2") == {"answer": "enhanced"}
        assert cache.get("query3") == {"answer": "deep"}

    def test_invalidate_by_strategy(self):
        """Test: Invalidate all entries with specific strategy."""
        # Arrange
        cache = ResponseCache()
        cache.set("query1", {"answer": "direct"}, strategy="direct")
        cache.set("query2", {"answer": "enhanced"}, strategy="enhanced")
        cache.set("query3", {"answer": "deep"}, strategy="deep_reasoning")
        cache.set("query4", {"answer": "direct2"}, strategy="direct")

        # Act - invalidate all direct strategy entries
        removed_count = cache.invalidate_by_strategy("direct")

        # Assert
        assert removed_count == 2
        assert cache.get("query1") is None
        assert cache.get("query4") is None
        assert cache.get("query2") == {"answer": "enhanced"}
        assert cache.get("query3") == {"answer": "deep"}