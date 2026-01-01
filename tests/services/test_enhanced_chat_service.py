"""
Tests for EnhancedChatService.

Tests helper methods and main processing flow with mocks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.enhanced_chat_service import EnhancedChatService
from app.core.agent_config import TaskType


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

class TestInferTaskType:
    """Tests for _infer_task_type()"""

    def setup_method(self):
        """Setup service with mocks."""
        self.service = EnhancedChatService(
            agent_service=MagicMock(),
            memory_service=MagicMock(),
            document_service=MagicMock(),
            web_search_service=MagicMock(),
        )

    def test_returns_code_analysis_for_code_keyword(self):
        """Test: returns CODE_ANALYSIS for code-related message."""
        result = self.service._infer_task_type("Fix this Python bug")
        assert result == TaskType.CODE_ANALYSIS

    def test_returns_medical_for_health_keyword(self):
        """Test: returns MEDICAL_QUERY for health-related message."""
        result = self.service._infer_task_type("What are symptoms of flu?")
        assert result == TaskType.MEDICAL_QUERY

    def test_returns_creative_for_write_keyword(self):
        """Test: returns CREATIVE_WRITING for creative request."""
        result = self.service._infer_task_type("Write me a short story")
        assert result == TaskType.CREATIVE_WRITING

    def test_returns_general_chat_for_default(self):
        """Test: returns GENERAL_CHAT for generic message."""
        result = self.service._infer_task_type("Hello, how are you?")
        assert result == TaskType.GENERAL_CHAT

class TestProcessMessage:
    """Tests for process_message()"""

    def setup_method(self):
        """Setup service with async mocks."""
        self.agent_service = MagicMock()
        self.agent_service.generate_response = AsyncMock(return_value={
            "response": "Test response",
            "tokens": 50
        })
        self.agent_service.select_best_agent_for_task = AsyncMock(return_value="mistral")

        self.memory_service = MagicMock()
        self.memory_service.get_conversation_history = AsyncMock(return_value=[])
        self.memory_service.search_facts = AsyncMock(return_value=[])
        self.memory_service.add_message = AsyncMock()

        self.document_service = MagicMock()
        self.document_service.search_documents = AsyncMock(return_value=[])

        self.web_search_service = MagicMock()
        self.web_search_service.search = AsyncMock(return_value=[])

        self.service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=self.document_service,
            web_search_service=self.web_search_service,
        )

    @pytest.mark.asyncio
    async def test_process_message_returns_response(self):
        """Test: process_message returns response dict."""
        result = await self.service.process_message(
            session_id="test-session-123",
            message="Hello world"
        )

        assert "response" in result
        assert "agent_used" in result
        assert "sources" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_process_message_auto_selects_agent(self):
        """Test: process_message auto-selects agent when not specified."""
        await self.service.process_message(
            session_id="test-session-123",
            message="Hello world"
        )

        self.agent_service.select_best_agent_for_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_uses_specified_agent(self):
        """Test: process_message uses specified agent without auto-select."""
        result = await self.service.process_message(
            session_id="test-session-123",
            message="Hello world",
            agent_name="deepseek"
        )

        assert result["agent_used"] == "deepseek"
        self.agent_service.select_best_agent_for_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_triggers_web_search(self):
        """Test: process_message searches web when keywords present."""
        self.web_search_service.search = AsyncMock(return_value=[
            {"title": "News", "snippet": "Latest news", "url": "http://example.com"}
        ])

        result = await self.service.process_message(
            session_id="test-session-123",
            message="What are the latest news today?"
        )

        self.web_search_service.search.assert_called_once()
        assert "web_search" in result["sources"]

    @pytest.mark.asyncio
    async def test_process_message_triggers_document_search(self):
        """Test: process_message searches documents when keywords present."""
        self.document_service.search_documents = AsyncMock(return_value=[
            {"text": "Document content", "metadata": {}}
        ])

        result = await self.service.process_message(
            session_id="test-session-123",
            message="Find my document about Python"
        )

        self.document_service.search_documents.assert_called_once()
        assert "documents" in result["sources"]

    @pytest.mark.asyncio
    async def test_process_message_includes_history(self):
        """Test: process_message includes conversation history."""
        mock_message = MagicMock()
        mock_message.role = "user"
        mock_message.content = "Previous message"

        self.memory_service.get_conversation_history = AsyncMock(return_value=[mock_message])

        result = await self.service.process_message(
            session_id="test-session-123",
            message="Hello again",
            include_memory=True
        )

        self.memory_service.get_conversation_history.assert_called_once()
        assert "conversation_history" in result["sources"]

    @pytest.mark.asyncio
    async def test_process_message_includes_facts(self):
        """Test: process_message includes relevant facts."""
        self.memory_service.search_facts = AsyncMock(return_value=[
            {"text": "User likes Python", "importance": 0.8},
            {"text": "User is a developer", "importance": 0.9},
        ])

        result = await self.service.process_message(
            session_id="test-session-123",
            message="Tell me about programming",
            include_memory=True
        )

        self.memory_service.search_facts.assert_called_once()
        assert "user_facts" in result["sources"]

    @pytest.mark.asyncio
    async def test_process_message_without_memory(self):
        """Test: process_message skips memory when include_memory=False."""
        result = await self.service.process_message(
            session_id="test-session-123",
            message="Hello",
            include_memory=False
        )

        self.memory_service.get_conversation_history.assert_not_called()
        self.memory_service.search_facts.assert_not_called()
        assert "conversation_history" not in result["sources"]

    @pytest.mark.asyncio
    async def test_process_message_saves_to_db(self):
        """Test: process_message saves messages when db provided."""
        mock_db = MagicMock()

        await self.service.process_message(
            session_id="test-session-123",
            message="Hello",
            include_memory=True,
            db=mock_db
        )

        # Should save user message and assistant response
        assert self.memory_service.add_message.call_count == 2

class TestExtractAndSaveFacts:
    """Tests for _extract_and_save_facts()"""

    def setup_method(self):
        """Setup service with mocks."""
        self.agent_service = MagicMock()
        self.memory_service = MagicMock()
        self.memory_service.add_facts = AsyncMock(return_value=[])

        self.service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=MagicMock(),
            web_search_service=MagicMock(),
        )

    @pytest.mark.asyncio
    async def test_returns_zero_when_disabled(self):
        """Test: returns 0 when memorisator disabled."""
        self.service.memorisator_enabled = False

        result = await self.service._extract_and_save_facts(
            session_id="test-123",
            user_message="Hello",
            assistant_message="Hi there"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_extractor(self):
        """Test: returns 0 when fact_extractor is None."""
        self.service.memorisator_enabled = True
        self.service.fact_extractor = None

        result = await self.service._extract_and_save_facts(
            session_id="test-123",
            user_message="Hello",
            assistant_message="Hi there"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        """Test: returns 0 and doesn't raise on exception."""
        self.service.memorisator_enabled = True
        self.service.fact_extractor = MagicMock()
        self.service.fact_extractor.extract_facts = AsyncMock(
            side_effect=Exception("Extraction failed")
        )

        result = await self.service._extract_and_save_facts(
            session_id="test-123",
            user_message="Hello",
            assistant_message="Hi there"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_extracts_and_saves_facts_successfully(self):
        """Test: extracts facts and saves them."""
        from app.services.memory_service import Fact

        mock_fact = MagicMock()
        mock_fact.importance = 0.8
        mock_fact.confidence = 0.9

        self.service.memorisator_enabled = True
        self.service.fact_extractor = MagicMock()
        self.service.fact_extractor.extract_facts = AsyncMock(return_value=[mock_fact])
        self.memory_service.add_facts = AsyncMock(return_value=[mock_fact])

        result = await self.service._extract_and_save_facts(
            session_id="test-123",
            user_message="My name is Denis",
            assistant_message="Nice to meet you, Denis!"
        )

        assert result == 1
        self.memory_service.add_facts.assert_called_once()