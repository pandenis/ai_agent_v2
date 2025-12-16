"""
Tests for ResponseFormatter - formats responses for better readability
"""
import pytest
from app.services.orchestrator.response_formatter import ResponseFormatter


class TestResponseFormatter:
    """Tests for response formatting"""

    def test_formatter_exists(self):
        """Test: ResponseFormatter class can be instantiated"""
        formatter = ResponseFormatter()
        assert formatter is not None

    def test_format_direct_single_fact(self):
        """Test: Single fact formatted as simple sentence"""
        formatter = ResponseFormatter()
        facts = [{"text": "User's name is Denis", "confidence": 0.95}]

        result = formatter.format_direct(facts)

        assert "Denis" in result
        assert result == "User's name is Denis."