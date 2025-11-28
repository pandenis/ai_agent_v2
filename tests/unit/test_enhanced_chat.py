"""
Tests for enhanced chat service with multi-source intelligence
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.enhanced_chat_service import EnhancedChatService


@pytest.fixture
def enhanced_chat_service():
    """Create enhanced chat service with mocked dependencies"""
    agent_service = MagicMock()
    agent_service.generate_response = AsyncMock(return_value={"status": "success", "response": "Test response", "tokens": 100})
    agent_service.select_best_agent_for_task = AsyncMock(return_value="mistral")

    memory_service = MagicMock()
    memory_service.get_conversation_history = AsyncMock(return_value=[])
    memory_service.search_facts = AsyncMock(return_value=[])
    memory_service.add_message = AsyncMock()

    document_service = MagicMock()
    document_service.search_documents = AsyncMock(return_value=[])

    web_search_service = MagicMock()
    web_search_service.search = AsyncMock(return_value=[])

    return EnhancedChatService(
        agent_service=agent_service,
        memory_service=memory_service,
        document_service=document_service,
        web_search_service=web_search_service,
    )


def test_should_search_documents(enhanced_chat_service):
    """Test document search trigger detection"""
    # Should trigger
    assert enhanced_chat_service._should_search_documents("What did I write in the document?")
    assert enhanced_chat_service._should_search_documents("Что я писал о FastAPI?")

    # Should not trigger
    assert not enhanced_chat_service._should_search_documents("Hello, how are you?")


def test_should_search_web(enhanced_chat_service):
    """Test web search trigger detection"""
    # Should trigger
    assert enhanced_chat_service._should_search_web("What are the latest news?")
    assert enhanced_chat_service._should_search_web("Current events in 2025")

    # Should not trigger
    assert not enhanced_chat_service._should_search_web("Hello, how are you?")


@pytest.mark.asyncio
async def test_process_message_basic(enhanced_chat_service):
    """Test basic message processing without search"""
    result = await enhanced_chat_service.process_message(
        session_id="test-session", message="Hello!", agent_name="mistral", include_memory=False
    )

    assert result["response"]
    assert result["agent_used"] == "mistral"
    assert result["sources"] == []
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_process_message_with_auto_agent_selection(enhanced_chat_service):
    """Test message processing with automatic agent selection"""
    result = await enhanced_chat_service.process_message(
        session_id="test-session", message="Hello!", agent_name=None, include_memory=False
    )

    assert result["response"]
    assert result["agent_used"] == "mistral"
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_process_message_with_document_search(enhanced_chat_service):
    """Test message processing with document search"""
    # Configure mock to return results
    enhanced_chat_service.document_service.search_documents.return_value = [
        {"text": "FastAPI is a web framework", "metadata": {}}
    ]

    result = await enhanced_chat_service.process_message(
        session_id="test-session", message="What did I write about FastAPI?", agent_name="mistral", include_memory=False
    )

    assert result["response"]
    assert "documents" in result["sources"]
    assert result["agent_used"] == "mistral"

    # Verify search was called
    enhanced_chat_service.document_service.search_documents.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_with_web_search(enhanced_chat_service):
    """Test message processing with web search"""
    # Configure mock to return results
    enhanced_chat_service.web_search_service.search.return_value = [
        {"title": "News", "snippet": "Latest news", "url": "http://example.com"}
    ]

    result = await enhanced_chat_service.process_message(
        session_id="test-session", message="What are the latest news in 2025?", agent_name="mistral", include_memory=False
    )

    assert result["response"]
    assert "web_search" in result["sources"]
    assert result["agent_used"] == "mistral"

    # Verify search was called
    enhanced_chat_service.web_search_service.search.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_with_memory(enhanced_chat_service):
    """Test message processing with memory integration"""
    # Configure mocks to return results
    enhanced_chat_service.memory_service.get_conversation_history.return_value = [
        {"role": "user", "content": "Previous message"}
    ]
    enhanced_chat_service.memory_service.search_facts.return_value = [{"text": "User prefers Python", "importance": 0.8}]

    result = await enhanced_chat_service.process_message(
        session_id="test-session", message="Hello!", agent_name="mistral", include_memory=True
    )

    assert result["response"]
    assert "conversation_history" in result["sources"]
    assert "user_facts" in result["sources"]


@pytest.mark.asyncio
async def test_infer_task_type(enhanced_chat_service):
    """Test task type inference from message"""
    from app.core.agent_config import TaskType

    # Code task
    task = enhanced_chat_service._infer_task_type("Write Python code")
    assert task == TaskType.CODE_ANALYSIS

    # Medical task
    task = enhanced_chat_service._infer_task_type("What are symptoms of flu?")
    assert task == TaskType.MEDICAL_QUERY

    # Creative writing
    task = enhanced_chat_service._infer_task_type("Write a story about dragons")
    assert task == TaskType.CREATIVE_WRITING

    # General chat
    task = enhanced_chat_service._infer_task_type("Hello, how are you?")
    assert task == TaskType.GENERAL_CHAT

@pytest.mark.asyncio
async def test_history_limit_truncates_history(enhanced_chat_service):
    enhanced_chat_service.memory_service.get_conversation_history.return_value = [
        {"role": "user", "content": f"Message {i}"} for i in range(10)
    ]

    enhanced_chat_service.history_limit = 3

    await enhanced_chat_service.process_message(
        session_id="test-ses",
        message="hi",
        agent_name="mistral",
        include_memory=True,
    )

    assert enhanced_chat_service.agent_service.generate_response.called
    prompt = enhanced_chat_service.agent_service.generate_response.call_args.kwargs["prompt"]

    assert "user: Message 7..." in prompt
    assert "user: Message 8..." in prompt
    assert "user: Message 9..." in prompt
    assert "user: Message 0..." not in prompt


