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

    def test_format_direct_multiple_facts(self):
        """Test: Multiple facts formatted as bullet list"""
        formatter = ResponseFormatter()
        facts = [
            {"text": "User's name is Denis", "confidence": 0.95},
            {"text": "Denis is a QA Engineer", "confidence": 0.90},
            {"text": "Denis loves Python", "confidence": 0.85}
        ]

        result = formatter.format_direct(facts)

        # Should have bullet points
        assert "•" in result
        # Should contain all facts
        assert "Denis" in result
        assert "QA Engineer" in result
        assert "Python" in result
        # Should have intro line
        assert "Here's what I know" in result or "know" in result.lower()