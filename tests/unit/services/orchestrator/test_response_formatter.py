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

    def test_format_enhanced_with_sources(self):
        """Test: Enhanced answers show AI + memory sources"""
        formatter = ResponseFormatter()
        ai_response = "Walking 30 minutes daily can help manage blood pressure."
        context_facts = [
            {"text": "User has high blood pressure", "confidence": 0.9}
        ]
        agent_name = "mixtral"

        result = formatter.format_enhanced(
            ai_response,
            context_facts,
            agent_name=agent_name,
            include_source=True
        )

        # Should include AI response
        assert "Walking" in result
        # Should include context
        assert "blood pressure" in result
        # Should show AI source
        assert "mixtral" in result.lower()
        # Should show memory source
        assert "memory" in result.lower()

    def test_format_deep_multi_paragraph(self):
        """Test: Deep reasoning supports paragraph breaks"""
        formatter = ResponseFormatter()
        long_response = """Climate change affects weather patterns in several ways.

    Rising global temperatures cause more extreme weather events. This includes stronger hurricanes, longer droughts, and more intense rainfall.

    Ocean temperatures also increase, affecting marine ecosystems. Coral reefs are particularly vulnerable to these changes."""

        result = formatter.format_deep(long_response)

        # Should preserve paragraph structure
        assert result.count("\n\n") >= 2
        # Should include all content
        assert "Climate change" in result
        assert "hurricanes" in result
        assert "Coral reefs" in result