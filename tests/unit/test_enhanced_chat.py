"""
Unit tests for enhanced chat service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.enhanced_chat_service import EnhancedChatService


@pytest.fixture
def mock_services():
    """Create mock services"""
    memory_service = AsyncMock()
    agent_service = AsyncMock()
    document_service = AsyncMock()
    web_search_service = AsyncMock()
    
    return {
        "memory": memory_service,
        "agent": agent_service,
        "document": document_service,
        "web": web_search_service
    }


@pytest.fixture
def enhanced_chat_service(mock_services):
    """Create enhanced chat service with mocks"""
    return EnhancedChatService(
        memory_service=mock_services["memory"],
        agent_service=mock_services["agent"],
        document_service=mock_services["document"],
        web_search_service=mock_services["web"]
    )


@pytest.mark.asyncio
async def test_should_search_documents(enhanced_chat_service):
    """Test document search detection"""
    assert enhanced_chat_service._should_search_documents("Check my document")
    assert enhanced_chat_service._should_search_documents("What did I write earlier?")
    assert not enhanced_chat_service._should_search_documents("Hello, how are you?")


@pytest.mark.asyncio
async def test_should_search_web(enhanced_chat_service):
    """Test web search detection"""
    assert enhanced_chat_service._should_search_web("What is the latest news?")
    assert enhanced_chat_service._should_search_web("Weather today")
    assert enhanced_chat_service._should_search_web("Who is the current president?")
    assert not enhanced_chat_service._should_search_web("Hello")


@pytest.mark.asyncio
async def test_process_message_basic(enhanced_chat_service, mock_services):
    """Test basic message processing"""
    # Setup mocks
    mock_services["memory"].get_conversation_history.return_value = []
    mock_services["memory"].get_important_facts.return_value = []
    mock_services["agent"].generate_response.return_value = {
        "status": "success",
        "response": "Hello! How can I help you?",
        "tokens": 10,
        "model": "mistral"
    }
    
    # Process message
    result = await enhanced_chat_service.process_message(
        session_id="test-123",
        message="Hello",
        include_memory=True
    )
    
    assert result["status"] == "success"
    assert "Hello" in result["response"]
    assert result["tokens"] == 10
    assert isinstance(result["sources_used"], list)


@pytest.mark.asyncio
async def test_process_message_with_document_search(enhanced_chat_service, mock_services):
    """Test message processing with document search"""
    # Setup mocks
    mock_services["memory"].get_conversation_history.return_value = []
    mock_services["memory"].get_important_facts.return_value = []
    mock_services["document"].search_documents.return_value = [
        {
            "id": "doc1",
            "text": "Important document content",
            "metadata": {"filename": "test.txt"}
        }
    ]
    mock_services["agent"].generate_response.return_value = {
        "status": "success",
        "response": "Based on your document...",
        "tokens": 20
    }
    
    # Process message with document keyword
    result = await enhanced_chat_service.process_message(
        session_id="test-123",
        message="What did I write in my document?",
        include_memory=True
    )
    
    assert result["status"] == "success"
    assert "documents" in result["sources_used"]
    mock_services["document"].search_documents.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_with_web_search(enhanced_chat_service, mock_services):
    """Test message processing with web search"""
    # Setup mocks
    mock_services["memory"].get_conversation_history.return_value = []
    mock_services["memory"].get_important_facts.return_value = []
    mock_services["web"].search.return_value = [
        {
            "title": "Latest AI News",
            "snippet": "Recent developments in AI...",
            "url": "https://example.com"
        }
    ]
    mock_services["agent"].generate_response.return_value = {
        "status": "success",
        "response": "According to recent news...",
        "tokens": 30
    }
    
    # Process message with web keyword
    result = await enhanced_chat_service.process_message(
        session_id="test-123",
        message="What are the latest AI news?",
        include_memory=True
    )
    
    assert result["status"] == "success"
    assert "web_search" in result["sources_used"]
    mock_services["web"].search.assert_called_once()
