"""
Tests for WebSearchService.

Uses mocks to avoid real DuckDuckGo API calls.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.web_search_service import WebSearchService


class TestWebSearchService:
    """Tests for WebSearchService.search()"""

    @patch.object(WebSearchService, '__init__', lambda self: None)
    def test_search_returns_results(self):
        """Test: search() returns formatted results."""
        service = WebSearchService()
        service.ddgs = MagicMock()
        service.ddgs.text.return_value = [
            {"title": "Weather Today", "body": "Sunny and warm", "href": "https://weather.com"},
            {"title": "Forecast", "body": "Weekly forecast", "href": "https://forecast.com"},
        ]

        import asyncio
        results = asyncio.run(service.search("weather today", max_results=2))

        assert len(results) == 2
        assert results[0]["title"] == "Weather Today"
        assert results[0]["snippet"] == "Sunny and warm"
        assert results[0]["url"] == "https://weather.com"
        assert results[0]["source"] == "duckduckgo"

    @patch.object(WebSearchService, '__init__', lambda self: None)
    def test_search_invalid_query_returns_error(self):
        """Test: search() with invalid query returns error."""
        service = WebSearchService()
        service.ddgs = MagicMock()

        import asyncio
        # Empty query should fail validation
        results = asyncio.run(service.search("", max_results=5))

        assert len(results) == 1
        assert "error" in results[0]
        assert "Invalid query" in results[0]["error"]

    @patch.object(WebSearchService, '__init__', lambda self: None)
    def test_search_exception_returns_error(self):
        """Test: search() handles exceptions gracefully."""
        service = WebSearchService()
        service.ddgs = MagicMock()
        service.ddgs.text.side_effect = Exception("Network error")

        import asyncio
        results = asyncio.run(service.search("weather", max_results=5))

        assert len(results) == 1
        assert "error" in results[0]
        assert "Network error" in results[0]["error"]
        assert "message" in results[0]

    @patch.object(WebSearchService, '__init__', lambda self: None)
    def test_search_dangerous_input_returns_error(self):
        """Test: search() with shell injection returns error."""
        service = WebSearchService()
        service.ddgs = MagicMock()

        import asyncio
        results = asyncio.run(service.search("test; rm -rf /", max_results=5))

        assert len(results) == 1
        assert "error" in results[0]

    @patch.object(WebSearchService, '__init__', lambda self: None)
    def test_search_empty_results(self):
        """Test: search() returns empty list when no results."""
        service = WebSearchService()
        service.ddgs = MagicMock()
        service.ddgs.text.return_value = []

        import asyncio
        results = asyncio.run(service.search("xyznonexistentquery123", max_results=5))

        assert results == []