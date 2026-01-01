"""
Tests for EnhancedChatService.

Tests helper methods and main processing flow with mocks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.enhanced_chat_service import EnhancedChatService


class TestShouldSearchDocuments:
    """Tests for _should_search_documents()"""

    def setup_method(self):
        """Setup service with mocks."""
        self.service = EnhancedChatService(
            agent_service=MagicMock(),
            memory_service=MagicMock(),
            document_service=MagicMock(),
            web_search_service=MagicMock(),
        )

    def test_returns_true_for_document_keyword(self):
        """Test: returns True when message contains 'document'."""
        assert self.service._should_search_documents("Find my document") is True

    def test_returns_true_for_file_keyword(self):
        """Test: returns True when message contains 'file'."""
        assert self.service._should_search_documents("Where is the file?") is True

    def test_returns_true_for_russian_keyword(self):
        """Test: returns True for Russian keyword 'документ'."""
        assert self.service._should_search_documents("Найди мой документ") is True

    def test_returns_false_for_no_keywords(self):
        """Test: returns False when no document keywords."""
        assert self.service._should_search_documents("What is the weather?") is False

class TestShouldSearchWeb:
    """Tests for _should_search_web()"""

    def setup_method(self):
        """Setup service with mocks."""
        self.service = EnhancedChatService(
            agent_service=MagicMock(),
            memory_service=MagicMock(),
            document_service=MagicMock(),
            web_search_service=MagicMock(),
        )

    def test_returns_true_for_latest_keyword(self):
        """Test: returns True when message contains 'latest'."""
        assert self.service._should_search_web("What are the latest news?") is True

    def test_returns_true_for_today_keyword(self):
        """Test: returns True when message contains 'today'."""
        assert self.service._should_search_web("What happened today?") is True

    def test_returns_true_for_russian_keyword(self):
        """Test: returns True for Russian keyword 'новости'."""
        assert self.service._should_search_web("Покажи новости") is True

    def test_returns_false_for_no_keywords(self):
        """Test: returns False when no web keywords."""
        assert self.service._should_search_web("Tell me about Python") is False