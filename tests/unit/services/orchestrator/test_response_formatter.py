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

    def test_format_direct_with_attribution(self):
        """Test: Direct answers show source (memory)"""
        formatter = ResponseFormatter()
        facts = [{"text": "User's name is Denis", "confidence": 0.95}]

        result = formatter.format_direct(facts, include_source=True)

        assert "Denis" in result
        assert "(from memory)" in result.lower()

    def test_format_direct_multiple_with_attribution(self):
        """Test: Multiple facts also show source"""
        formatter = ResponseFormatter()
        facts = [
            {"text": "User's name is Denis", "confidence": 0.95},
            {"text": "Denis is a QA Engineer", "confidence": 0.90}
        ]

        result = formatter.format_direct(facts, include_source=True)

        assert "•" in result
        assert "(from memory)" in result.lower()

    def test_format_enhanced_with_context(self):
        """Test: Enhanced answers include context from memory"""
        formatter = ResponseFormatter()
        ai_response = "The Mediterranean diet is excellent for heart health."
        context_facts = [
            {"text": "User has high blood pressure", "confidence": 0.9},
            {"text": "User's doctor recommended dietary changes", "confidence": 0.85}
        ]

        result = formatter.format_enhanced(ai_response, context_facts)

        # Should include AI response
        assert "Mediterranean diet" in result
        # Should include context header
        assert "Based on" in result or "Context:" in result or "know about you" in result
        # Should include facts
        assert "blood pressure" in result
        assert "doctor" in result