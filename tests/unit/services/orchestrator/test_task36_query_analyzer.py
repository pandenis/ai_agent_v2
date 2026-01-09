"""
Task 36: QueryAnalyzer should extract meaningful topics from personal questions
"""
import pytest
from app.services.orchestrator.query_analyzer import QueryAnalyzer


class TestQueryAnalyzerTopicExtraction:
    """Tests for improved topic extraction."""

    def test_extracts_name_topic_from_name_question(self):
        """What is my name? should extract 'name' as topic."""
        qa = QueryAnalyzer()
        result = qa.analyze("What is my name?")

        # Should contain 'name' or similar, not just 'general'
        assert 'name' in result.topics or 'identity' in result.topics, \
            f"Expected 'name' or 'identity' in topics, got {result.topics}"

    def test_extracts_profession_topic(self):
        """What is my profession? should extract relevant topic."""
        qa = QueryAnalyzer()
        result = qa.analyze("What is my profession?")

        assert any(t in result.topics for t in ['profession', 'job', 'work', 'career']), \
            f"Expected profession-related topic, got {result.topics}"

    def test_extracts_location_topic(self):
        """Where do I live? should extract location topic."""
        qa = QueryAnalyzer()
        result = qa.analyze("Where do I live?")

        assert any(t in result.topics for t in ['location', 'live', 'address', 'home']), \
            f"Expected location-related topic, got {result.topics}"

    def test_extracts_preference_topic(self):
        """What is my favorite color? should extract preference topic."""
        qa = QueryAnalyzer()
        result = qa.analyze("What is my favorite color?")

        assert any(t in result.topics for t in ['favorite', 'preference', 'color']), \
            f"Expected preference-related topic, got {result.topics}"