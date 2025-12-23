"""Tests for ResponseCache component"""
import pytest
import time
from app.services.orchestrator.response_cache import ResponseCache


class TestResponseCache:
    """Test suite for ResponseCache"""

    def test_cache_hit_returns_stored_response(self):
        """Test: Cache should return stored response on hit"""
        # Arrange - universal example (weather query, not programming!)
        cache = ResponseCache()
        query = "What's the weather in Tokyo?"
        session_id = "weather-session-123"
        expected_response = {
            "text": "It's sunny and 22°C in Tokyo",
            "metadata": {"strategy": "enhanced", "confidence": 0.9}
        }

        # Store response in cache
        cache.set(query, session_id, expected_response)

        # Act - retrieve from cache
        result = cache.get(query, session_id)

        # Assert
        assert result is not None
        assert result["text"] == expected_response["text"]
        assert result["metadata"]["strategy"] == "enhanced"