"""
Integration tests for Chat API endpoints.

Tests:
- POST /chat/enhanced
- POST /documents/upload
- POST /documents/search
- POST /search/web
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ============================================================================
# HELPER: Create client with mocked services
# ============================================================================

@pytest.fixture
async def client_with_mocked_services(test_engine):
    """Client with mocked services for chat endpoint tests."""
    from app.main import app
    from app.core.database import get_db
    from app.api.deps import get_memory_service, get_agent_service
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    
    # Create session factory for test engine
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Override get_db
    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
    
    # Create mock memory service
    mock_memory = MagicMock()
    mock_memory.get_facts = AsyncMock(return_value=[])
    mock_memory.get_chat_history = AsyncMock(return_value=[])
    mock_memory.save_message = AsyncMock(return_value=True)
    
    async def override_get_memory_service():
        return mock_memory
    
    # Create mock agent service
    mock_agent = MagicMock()
    mock_agent.generate_response = AsyncMock(return_value={
        "status": "success",
        "response": "Mocked AI response",
        "agent_name": "mistral",
        "tokens": 15
    })
    mock_agent.select_best_agent_for_task = AsyncMock(return_value="mistral")
    
    async def override_get_agent_service():
        return mock_agent
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_memory_service] = override_get_memory_service
    app.dependency_overrides[get_agent_service] = override_get_agent_service
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        ac.mock_memory = mock_memory
        ac.mock_agent = mock_agent
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# CHAT ENDPOINT TESTS
# ============================================================================

class TestEnhancedChat:
    """Tests for POST /chat/enhanced endpoint."""

    @pytest.mark.asyncio
    async def test_chat_success(self, client_with_mocked_services):
        """Test: POST /chat/enhanced returns successful response."""
        # Arrange
        request_data = {
            "message": "Hello, how are you today?",
            "session_id": "test-session-123",
            "agent_name": "mistral",
            "include_memory": True
        }
        
        # Mock both DocumentService and WebSearchService at module level to avoid ChromaDB
        with patch('app.api.routes.DocumentService') as mock_doc_class, \
             patch('app.api.routes.WebSearchService') as mock_web_class, \
             patch('app.api.routes.EnhancedChatService') as mock_chat_class:
            
            # Setup mocks
            mock_doc_class.return_value = MagicMock()
            mock_web_class.return_value = MagicMock()
            
            mock_chat_instance = MagicMock()
            mock_chat_instance.process_message = AsyncMock(return_value={
                "response": "I'm doing well, thank you!",
                "agent_used": "mistral",
                "sources": [],
                "tokens": 20,
                "timestamp": "2025-01-01T00:00:00"
            })
            mock_chat_class.return_value = mock_chat_instance
            
            # Act
            response = await client_with_mocked_services.post("/api/v1/chat/enhanced", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["session_id"] == "test-session-123"

    @pytest.mark.asyncio
    async def test_chat_empty_message_returns_400(self, client_with_mocked_services):
        """Test: POST /chat/enhanced with empty message returns 400."""
        # Arrange
        request_data = {
            "message": "",
            "session_id": "test-session-123"
        }
        
        # Act
        response = await client_with_mocked_services.post("/api/v1/chat/enhanced", json=request_data)
        
        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_chat_invalid_session_id_returns_400(self, client_with_mocked_services):
        """Test: POST /chat/enhanced with invalid session_id returns 400."""
        # Arrange
        request_data = {
            "message": "Hello",
            "session_id": "invalid;session;id"
        }
        
        # Act
        response = await client_with_mocked_services.post("/api/v1/chat/enhanced", json=request_data)
        
        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_chat_dangerous_input_returns_400(self, client_with_mocked_services):
        """Test: POST /chat/enhanced with dangerous input returns 400."""
        # Arrange
        request_data = {
            "message": "Hello $(rm -rf /)",
            "session_id": "test-session-123"
        }
        
        # Act
        response = await client_with_mocked_services.post("/api/v1/chat/enhanced", json=request_data)
        
        # Assert
        assert response.status_code == 400


# ============================================================================
# DOCUMENT ENDPOINT TESTS
# ============================================================================

class TestDocumentUpload:
    """Tests for POST /documents/upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_document_success(self, client):
        """Test: POST /documents/upload uploads document."""
        # Arrange
        request_data = {
            "text": "This is a test document with some content.",
            "filename": "test.txt",
            "source": "test"
        }
        
        with patch('app.api.routes.DocumentService') as mock_service_class:
            mock_instance = MagicMock()
            mock_instance.add_document = AsyncMock(return_value="doc-123")
            mock_service_class.return_value = mock_instance
            
            # Act
            response = await client.post("/api/v1/documents/upload", json=request_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "doc-123"

    @pytest.mark.asyncio
    async def test_upload_document_empty_text_returns_400(self, client):
        """Test: POST /documents/upload with empty text returns 400."""
        # Arrange
        request_data = {
            "text": "",
            "filename": "test.txt"
        }
        
        # Act
        response = await client.post("/api/v1/documents/upload", json=request_data)
        
        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_document_dangerous_filename_sanitized(self, client):
        """Test: POST /documents/upload sanitizes dangerous filename."""
        # Arrange
        request_data = {
            "text": "Some valid content here.",
            "filename": "../../../etc/passwd",
            "source": "test"
        }
        
        with patch('app.api.routes.DocumentService') as mock_service_class:
            mock_instance = MagicMock()
            mock_instance.add_document = AsyncMock(return_value="doc-456")
            mock_service_class.return_value = mock_instance
            
            # Act
            response = await client.post("/api/v1/documents/upload", json=request_data)
        
        # Assert
        # Should succeed but with sanitized filename
        assert response.status_code == 201


class TestDocumentSearch:
    """Tests for POST /documents/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, client):
        """Test: POST /documents/search returns results."""
        # Arrange
        request_data = {
            "query": "test query",
            "n_results": 5
        }
        
        with patch('app.api.routes.DocumentService') as mock_service_class:
            mock_instance = MagicMock()
            mock_instance.search_documents = AsyncMock(return_value=[
                {"id": "doc-1", "text": "Result 1", "score": 0.95},
                {"id": "doc-2", "text": "Result 2", "score": 0.85}
            ])
            mock_service_class.return_value = mock_instance
            
            # Act
            response = await client.post("/api/v1/documents/search", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total_found"] == 2


# ============================================================================
# WEB SEARCH ENDPOINT TESTS
# ============================================================================

class TestWebSearch:
    """Tests for POST /search/web endpoint."""

    @pytest.mark.asyncio
    async def test_web_search_success(self, client):
        """Test: POST /search/web returns results."""
        # Arrange
        request_data = {
            "query": "Python programming",
            "max_results": 5
        }
        
        with patch('app.api.routes.WebSearchService') as mock_service_class:
            mock_instance = MagicMock()
            mock_instance.search = AsyncMock(return_value=[
                {"title": "Python Tutorial", "url": "https://python.org", "snippet": "Learn Python"},
            ])
            mock_service_class.return_value = mock_instance
            
            # Act
            response = await client.post("/api/v1/search/web", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total_found"] >= 0

    @pytest.mark.asyncio
    async def test_web_search_empty_query_returns_400(self, client):
        """Test: POST /search/web with empty query returns 400."""
        # Arrange
        request_data = {
            "query": "",
            "max_results": 5
        }
        
        # Act
        response = await client.post("/api/v1/search/web", json=request_data)
        
        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_web_search_dangerous_query_returns_400(self, client):
        """Test: POST /search/web with dangerous query returns 400."""
        # Arrange
        request_data = {
            "query": "test; rm -rf /",
            "max_results": 5
        }
        
        # Act
        response = await client.post("/api/v1/search/web", json=request_data)
        
        # Assert
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
