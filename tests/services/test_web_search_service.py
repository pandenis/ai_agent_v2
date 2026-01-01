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