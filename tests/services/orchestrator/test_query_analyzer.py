"""Tests for QueryAnalyzer component"""
import pytest
from app.services.orchestrator.query_analyzer import QueryAnalyzer, QueryAnalysis


class TestQueryAnalyzer:
    """Test suite for QueryAnalyzer"""

    def test_simple_query_what_is_my_name(self):
        """Test: Simple question 'What is my name?' should be classified as simple"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "What is my name?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert isinstance(result, QueryAnalysis)
        assert result.complexity == "simple"
        assert result.requires_memory == True
        assert result.requires_reasoning == False