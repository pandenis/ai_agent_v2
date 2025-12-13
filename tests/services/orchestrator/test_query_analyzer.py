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

    def test_greeting_simple(self):
        """Test: Greetings should be simple"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Hello!"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.complexity == "simple"
        assert result.requires_reasoning == False

    def test_medical_topic(self):
        """Test: Should identify medical topic"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "What are the symptoms of flu?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert "medical" in result.topics
        assert "symptom" in result.entities

    def test_multiple_topics(self):
        """Test: Can identify multiple topics"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Analyze the Python code for medical diagnosis system"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert "programming" in result.topics
        assert "medical" in result.topics
        assert "analysis" in result.topics

    def test_intent_question(self):
        """Test: Questions should be identified as 'question' intent"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "How does photosynthesis work?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.intent == "question"

    def test_intent_command(self):
        """Test: Commands should be identified as 'command' intent"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Translate this text to French"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.intent == "command"

    def test_intent_statement(self):
        """Test: Statements should be identified as 'statement' intent"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Dogs are loyal animals"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.intent == "statement"

    def test_query_type_factual(self):
        """Test: Factual questions should be 'factual' type"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "What is the capital of France?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.query_type == "factual"

    def test_query_type_reasoning(self):
        """Test: Why questions should be 'reasoning' type"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Why do birds migrate south in winter?"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.query_type == "reasoning"

    def test_query_type_creative(self):
        """Test: Creative requests should be 'creative' type"""
        # Arrange
        analyzer = QueryAnalyzer()
        query = "Write a poem about the ocean"

        # Act
        result = analyzer.analyze(query)

        # Assert
        assert result.query_type == "creative"