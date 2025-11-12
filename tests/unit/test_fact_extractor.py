"""
Unit tests for FactExtractor service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.fact_extractor import FactExtractor
from app.models.memory_v2 import Fact


@pytest.fixture
def mock_agent_service():
    """Mock AgentService for testing"""
    service = MagicMock()
    service.generate_response = AsyncMock()
    return service


@pytest.fixture
def fact_extractor(mock_agent_service):
    """Create FactExtractor with mocked AgentService"""
    return FactExtractor(agent_service=mock_agent_service)


class TestFactExtractor:
    """Tests for FactExtractor class"""

    @pytest.mark.asyncio
    async def test_extract_facts_success(self, fact_extractor, mock_agent_service):
        """Test successful fact extraction"""
        # Mock response
        mock_agent_service.generate_response.return_value = {
            "status": "success",
            "response": '{"facts": [{"text": "User loves Python", "importance": 0.8, "confidence": 0.9, "fact_type": "preference", "tags": ["python"]}]}'
        }

        messages = [{"role": "user", "content": "I love Python"}]
        facts = await fact_extractor.extract_facts(messages)

        assert len(facts) == 1
        assert facts[0].text == "User loves Python"
        assert facts[0].importance == 0.8
        assert facts[0].confidence == 0.9
        assert facts[0].fact_type == "preference"
        assert "python" in facts[0].tags

    @pytest.mark.asyncio
    async def test_extract_facts_empty_result(self, fact_extractor, mock_agent_service):
        """Test extraction with no facts found"""
        mock_agent_service.generate_response.return_value = {
            "status": "success",
            "response": '{"facts": []}'
        }

        messages = [{"role": "user", "content": "Hello"}]
        facts = await fact_extractor.extract_facts(messages)

        assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_extract_facts_generation_failure(self, fact_extractor, mock_agent_service):
        """Test extraction when generation fails"""
        mock_agent_service.generate_response.return_value = {
            "status": "error",
            "error": "Model unavailable"
        }

        messages = [{"role": "user", "content": "Test"}]
        facts = await fact_extractor.extract_facts(messages)

        assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_extract_facts_invalid_json(self, fact_extractor, mock_agent_service):
        """Test extraction with invalid JSON response"""
        mock_agent_service.generate_response.return_value = {
            "status": "success",
            "response": "Not valid JSON"
        }

        messages = [{"role": "user", "content": "Test"}]
        facts = await fact_extractor.extract_facts(messages)

        assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_extract_facts_with_markdown(self, fact_extractor, mock_agent_service):
        """Test extraction with markdown code blocks"""
        mock_agent_service.generate_response.return_value = {
            "status": "success",
            "response": '```json\n{"facts": [{"text": "Test fact", "importance": 0.7, "confidence": 0.8, "fact_type": "static", "tags": []}]}\n```'
        }

        messages = [{"role": "user", "content": "Test"}]
        facts = await fact_extractor.extract_facts(messages)

        assert len(facts) == 1
        assert facts[0].text == "Test fact"

    @pytest.mark.asyncio
    async def test_extract_facts_multiple(self, fact_extractor, mock_agent_service):
        """Test extraction of multiple facts"""
        mock_agent_service.generate_response.return_value = {
            "status": "success",
            "response": '''{
                "facts": [
                    {"text": "Fact 1", "importance": 0.8, "confidence": 0.9, "fact_type": "static", "tags": ["tag1"]},
                    {"text": "Fact 2", "importance": 0.7, "confidence": 0.8, "fact_type": "preference", "tags": ["tag2"]},
                    {"text": "Fact 3", "importance": 0.9, "confidence": 1.0, "fact_type": "event", "tags": []}
                ]
            }'''
        }

        messages = [{"role": "user", "content": "Multiple facts"}]
        facts = await fact_extractor.extract_facts(messages)

        assert len(facts) == 3
        assert facts[0].fact_type == "static"
        assert facts[1].fact_type == "preference"
        assert facts[2].fact_type == "event"

    @pytest.mark.asyncio
    async def test_extract_from_text(self, fact_extractor, mock_agent_service):
        """Test convenience method extract_from_text"""
        mock_agent_service.generate_response.return_value = {
            "status": "success",
            "response": '{"facts": [{"text": "Test", "importance": 0.5, "confidence": 0.8, "fact_type": "static", "tags": []}]}'
        }

        facts = await fact_extractor.extract_from_text("Single text input")

        assert len(facts) == 1

    def test_format_messages(self, fact_extractor):
        """Test message formatting"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]

        formatted = fact_extractor._format_messages(messages)

        assert "User: Hello" in formatted
        assert "Assistant: Hi there" in formatted
        assert "User: How are you?" in formatted

    def test_validate_score_valid(self, fact_extractor):
        """Test score validation with valid values"""
        assert fact_extractor._validate_score(0.5) == 0.5
        assert fact_extractor._validate_score(0.0) == 0.0
        assert fact_extractor._validate_score(1.0) == 1.0

    def test_validate_score_clamping(self, fact_extractor):
        """Test score validation clamping"""
        assert fact_extractor._validate_score(-0.5) == 0.0
        assert fact_extractor._validate_score(1.5) == 1.0
        assert fact_extractor._validate_score(100) == 1.0

    def test_validate_score_invalid_type(self, fact_extractor):
        """Test score validation with invalid types"""
        assert fact_extractor._validate_score("invalid") == 0.5
        assert fact_extractor._validate_score(None) == 0.5
        assert fact_extractor._validate_score([]) == 0.5

    def test_create_fact_from_dict_valid(self, fact_extractor):
        """Test creating Fact from valid dictionary"""
        fact_data = {
            "text": "Test fact",
            "importance": 0.8,
            "confidence": 0.9,
            "fact_type": "static",
            "tags": ["test"]
        }

        fact = fact_extractor._create_fact_from_dict(fact_data)

        assert fact is not None
        assert fact.text == "Test fact"
        assert fact.importance == 0.8
        assert fact.confidence == 0.9
        assert fact.fact_type == "static"
        assert "test" in fact.tags
        assert fact.source == "conversation"

    def test_create_fact_from_dict_minimal(self, fact_extractor):
        """Test creating Fact with only required fields"""
        fact_data = {"text": "Minimal fact"}

        fact = fact_extractor._create_fact_from_dict(fact_data)

        assert fact is not None
        assert fact.text == "Minimal fact"
        assert fact.importance == 0.5  # default
        assert fact.confidence == 0.8  # default
        assert fact.fact_type == "static"  # default

    def test_create_fact_from_dict_missing_text(self, fact_extractor):
        """Test creating Fact without text (should fail)"""
        fact_data = {"importance": 0.8}

        fact = fact_extractor._create_fact_from_dict(fact_data)

        assert fact is None

    def test_create_fact_from_dict_with_defaults(self, fact_extractor):
        """Test creating Fact uses defaults for missing fields"""
        fact_data = {
            "text": "Test",
            "importance": 1.5,  # Will be clamped
            "confidence": -0.5  # Will be clamped
        }

        fact = fact_extractor._create_fact_from_dict(fact_data)

        assert fact.importance == 1.0  # clamped
        assert fact.confidence == 0.0  # clamped

    def test_parse_extraction_result_valid(self, fact_extractor):
        """Test parsing valid extraction result"""
        response = '{"facts": [{"text": "Test", "importance": 0.7, "confidence": 0.8, "fact_type": "static", "tags": []}]}'

        facts = fact_extractor._parse_extraction_result(response)

        assert len(facts) == 1
        assert facts[0].text == "Test"

    def test_parse_extraction_result_missing_facts_key(self, fact_extractor):
        """Test parsing result without 'facts' key"""
        response = '{"data": []}'

        facts = fact_extractor._parse_extraction_result(response)

        assert len(facts) == 0

    def test_parse_extraction_result_facts_not_list(self, fact_extractor):
        """Test parsing result where 'facts' is not a list"""
        response = '{"facts": "not a list"}'

        facts = fact_extractor._parse_extraction_result(response)

        assert len(facts) == 0

    def test_parse_extraction_result_with_invalid_facts(self, fact_extractor):
        """Test parsing result with some invalid facts"""
        response = '''{
            "facts": [
                {"text": "Valid fact", "importance": 0.8, "confidence": 0.9, "fact_type": "static", "tags": []},
                {"importance": 0.7},
                {"text": "Another valid", "importance": 0.6, "confidence": 0.7, "fact_type": "preference", "tags": []}
            ]
        }'''

        facts = fact_extractor._parse_extraction_result(response)

        # Should only parse valid facts
        assert len(facts) == 2
        assert facts[0].text == "Valid fact"
        assert facts[1].text == "Another valid"

    def test_get_system_prompt(self, fact_extractor):
        """Test system prompt generation"""
        prompt = fact_extractor._get_system_prompt()

        assert "fact extraction" in prompt.lower()
        assert "JSON" in prompt
        assert "importance" in prompt
        assert "confidence" in prompt

    def test_build_extraction_prompt(self, fact_extractor):
        """Test extraction prompt building"""
        messages = [
            {"role": "user", "content": "I love programming"},
            {"role": "assistant", "content": "That's great!"}
        ]

        prompt = fact_extractor._build_extraction_prompt(messages)

        assert "I love programming" in prompt
        assert "That's great!" in prompt
        assert "JSON" in prompt

    @pytest.mark.asyncio
    async def test_extract_facts_exception_handling(self, fact_extractor, mock_agent_service):
        """Test that exceptions are handled gracefully"""
        mock_agent_service.generate_response.side_effect = Exception("Test error")

        messages = [{"role": "user", "content": "Test"}]
        facts = await fact_extractor.extract_facts(messages)

        # Should return empty list, not raise exception
        assert len(facts) == 0

    def test_fact_has_uuid(self, fact_extractor):
        """Test that created facts have valid UUIDs"""
        fact_data = {"text": "Test fact"}
        fact = fact_extractor._create_fact_from_dict(fact_data)

        assert fact is not None
        assert fact.fact_id is not None
        assert len(fact.fact_id) == 36  # UUID length with hyphens

    def test_fact_has_timestamps(self, fact_extractor):
        """Test that created facts have timestamps"""
        fact_data = {"text": "Test fact"}
        fact = fact_extractor._create_fact_from_dict(fact_data)

        assert fact is not None
        assert isinstance(fact.created, datetime)
        assert isinstance(fact.updated, datetime)