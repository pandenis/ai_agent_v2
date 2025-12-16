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