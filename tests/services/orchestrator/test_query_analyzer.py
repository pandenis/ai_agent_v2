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

    def test_complex_query_compare(self):
        """Test: Complex question with 'compare' should be classified as complex"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Compare quantum computing with classical computing"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.complexity == "complex"
        assert result.requires_reasoning == True

    def test_medium_query_how_to(self):
        """Test: 'How to' questions should be classified as medium"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "How to fix a Python bug?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.complexity == "medium"
        assert result.requires_memory == True

    def test_entity_extraction_python_bug(self):
        """Test: Should extract 'Python' and 'bug' as entities"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "How to fix a Python bug?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert "Python" in result.entities
        assert "bug" in result.entities

    def test_topic_extraction_programming(self):
        """Test: Should identify 'programming' as topic for Python bug question"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "How to fix a Python bug?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert "programming" in result.topics