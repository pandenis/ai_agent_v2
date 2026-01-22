"""
Tests for EnhancedChatService fact handling
TDD: BUG-01 - Fact objects treated as dicts
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests"""
    with patch("app.services.enhanced_chat_service.settings") as mock:
        mock.memorisator_enabled = False
        mock.fact_importance_threshold = 0.5
        mock.fact_confidence_threshold = 0.7
        yield mock


@pytest.fixture
def mock_services():
    """Create mock services for testing"""
    return {
        "agent_service": AsyncMock(),
        "memory_service": AsyncMock(),
        "document_service": AsyncMock(),
        "web_search_service": AsyncMock(),
    }


@pytest.fixture
def sample_fact_models():
    """
    Create sample FactModel-like objects (NOT dicts!)
    Simulates what MemoryService.search_facts() actually returns.
    """
    fact1 = MagicMock()
    fact1.fact_id = "fact-1"
    fact1.text = "User's name is Denis"
    fact1.importance = 0.9
    fact1.confidence = 0.95
    fact1.tags = ["name", "identity"]
    fact1.fact_type = "static"
    del fact1.get  # Remove .get() to simulate real FactModel

    fact2 = MagicMock()
    fact2.fact_id = "fact-2"
    fact2.text = "User is a QA Engineer"
    fact2.importance = 0.8
    fact2.confidence = 0.9
    fact2.tags = ["profession"]
    fact2.fact_type = "static"
    del fact2.get

    fact3 = MagicMock()
    fact3.fact_id = "fact-3"
    fact3.text = "User likes Python"
    fact3.importance = 0.7
    fact3.confidence = 0.85
    fact3.tags = ["preference"]
    fact3.fact_type = "preference"
    del fact3.get

    return [fact1, fact2, fact3]


class TestEnhancedChatServiceFactHandling:
    """Tests for correct handling of FactModel objects"""

    @pytest.mark.asyncio
    async def test_process_message_handles_factmodel_objects(
            self, mock_services, sample_fact_models
    ):
        """
        Test: process_message correctly handles FactModel objects
        BUG-01: Code was using f.get() and f['text'] which fails on FactModel
        """
        from app.services.enhanced_chat_service import EnhancedChatService

        # Arrange
        mock_services["memory_service"].search_facts.return_value = sample_fact_models
        mock_services["memory_service"].get_conversation_history.return_value = []
        mock_services["document_service"].search_documents.return_value = []
        mock_services["web_search_service"].search.return_value = []
        mock_services["agent_service"].generate_response.return_value = {
            "response": "Hello Denis!",
            "model": "mistral",
            "tokens": 10,
        }
        mock_services["agent_service"].select_best_agent_for_task.return_value = "mistral"

        service = EnhancedChatService(**mock_services)

        # Act - Should NOT raise AttributeError or TypeError
        result = await service.process_message(
            session_id="test-session",
            message="What is my name?",
            include_memory=True,
        )

        # Assert
        assert result is not None
        assert "response" in result
        mock_services["memory_service"].search_facts.assert_called_once()

    @pytest.mark.asyncio
    async def test_fact_text_in_context(self, mock_services, sample_fact_models):
        """
        Test: Fact text appears in the enhanced prompt sent to agent
        """
        from app.services.enhanced_chat_service import EnhancedChatService

        # Arrange
        mock_services["memory_service"].search_facts.return_value = sample_fact_models[:1]
        mock_services["memory_service"].get_conversation_history.return_value = []
        mock_services["document_service"].search_documents.return_value = []
        mock_services["web_search_service"].search.return_value = []

        captured_prompt = None

        async def capture_prompt(prompt, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return {"response": "Test", "model": "mistral", "tokens": 5}

        mock_services["agent_service"].generate_response.side_effect = capture_prompt
        mock_services["agent_service"].select_best_agent_for_task.return_value = "mistral"

        service = EnhancedChatService(**mock_services)

        # Act
        await service.process_message(
            session_id="test-session",
            message="What do you know about me?",
            include_memory=True,
        )

        # Assert - fact text should be in the enhanced prompt
        assert captured_prompt is not None
        assert "User's name is Denis" in captured_prompt

    @pytest.mark.asyncio
    async def test_empty_facts_handled(self, mock_services):
        """Test: Empty facts list doesn't cause errors"""
        from app.services.enhanced_chat_service import EnhancedChatService

        mock_services["memory_service"].search_facts.return_value = []
        mock_services["memory_service"].get_conversation_history.return_value = []
        mock_services["document_service"].search_documents.return_value = []
        mock_services["web_search_service"].search.return_value = []
        mock_services["agent_service"].generate_response.return_value = {
            "response": "I don't know yet.",
            "model": "mistral",
            "tokens": 10,
        }
        mock_services["agent_service"].select_best_agent_for_task.return_value = "mistral"

        service = EnhancedChatService(**mock_services)

        result = await service.process_message(
            session_id="test-session",
            message="What is my name?",
            include_memory=True,
        )

        assert result is not None