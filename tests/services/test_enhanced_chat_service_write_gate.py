"""
Tests for EnhancedChatService with MemoryWriteGate integration

Epic 2: Memory Write Centralization
Task 2.3: Refactor EnhancedChatService to emit write commands (not direct writes)

Why this exists:
- EnhancedChatService should use MemoryWriteGate for all memory writes
- Facts must have thread_id set to session_id for isolation
- All writes should go through centralized gate for validation/audit
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models.memory_v2 import Fact
from app.schemas.memory_commands import MemoryWriteCommand
from app.services.enhanced_chat_service import EnhancedChatService


class TestEnhancedChatServiceWithWriteGate:
    """Test EnhancedChatService uses MemoryWriteGate for writes."""

    def setup_method(self):
        """Setup service with mocks."""
        self.agent_service = MagicMock()
        self.memory_service = MagicMock()
        self.memory_service.add_facts = AsyncMock(return_value=[])
        self.memory_service.get_conversation_history = AsyncMock(return_value=[])
        self.memory_service.search_facts = AsyncMock(return_value=[])

        # Mock write gate
        self.write_gate = MagicMock()
        self.write_gate.execute = AsyncMock(return_value=MagicMock(
            success=True,
            facts_written=1,
            fact_ids=["test-fact-1"]
        ))

    def test_accepts_write_gate_parameter(self):
        """Test: EnhancedChatService accepts write_gate parameter."""
        service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=MagicMock(),
            web_search_service=MagicMock(),
            write_gate=self.write_gate
        )

        assert service.write_gate == self.write_gate

    def test_write_gate_is_optional(self):
        """Test: write_gate parameter is optional for backward compatibility."""
        service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=MagicMock(),
            web_search_service=MagicMock(),
            # No write_gate provided
        )

        assert service.write_gate is None


class TestExtractAndSaveFactsWithGate:
    """Test _extract_and_save_facts uses MemoryWriteGate."""

    def setup_method(self):
        """Setup service with mocks."""
        self.agent_service = MagicMock()
        self.memory_service = MagicMock()
        self.memory_service.add_facts = AsyncMock(return_value=[])

        # Mock write gate
        self.write_gate = MagicMock()
        self.write_gate.execute = AsyncMock(return_value=MagicMock(
            success=True,
            facts_written=2,
            fact_ids=["fact-1", "fact-2"]
        ))

        self.service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=MagicMock(),
            web_search_service=MagicMock(),
            write_gate=self.write_gate
        )

        # Enable memorisator
        self.service.memorisator_enabled = True

        # Mock fact extractor
        self.mock_fact = MagicMock(spec=Fact)
        self.mock_fact.importance = 0.8
        self.mock_fact.confidence = 0.9
        self.mock_fact.thread_id = None  # Will be set by service

        self.service.fact_extractor = MagicMock()
        self.service.fact_extractor.extract_facts = AsyncMock(
            return_value=[self.mock_fact]
        )

    @pytest.mark.asyncio
    async def test_uses_write_gate_when_provided(self):
        """Test: _extract_and_save_facts uses write_gate.execute when gate is provided."""
        await self.service._extract_and_save_facts(
            session_id="test-session-123",
            user_message="My name is Denis",
            assistant_message="Nice to meet you, Denis!"
        )

        # Should call write_gate.execute, NOT memory_service.add_facts directly
        self.write_gate.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_write_command_with_correct_thread_id(self):
        """Test: Creates MemoryWriteCommand with thread_id = session_id."""
        session_id = "session-abc-123"

        await self.service._extract_and_save_facts(
            session_id=session_id,
            user_message="Hello",
            assistant_message="Hi there"
        )

        # Get the command that was passed to execute
        call_args = self.write_gate.execute.call_args
        command = call_args[0][0]  # First positional argument

        assert isinstance(command, MemoryWriteCommand)
        assert command.thread_id == session_id

    @pytest.mark.asyncio
    async def test_creates_write_command_with_correct_source(self):
        """Test: Creates MemoryWriteCommand with source='chat_service'."""
        await self.service._extract_and_save_facts(
            session_id="test-session",
            user_message="Hello",
            assistant_message="Hi"
        )

        call_args = self.write_gate.execute.call_args
        command = call_args[0][0]

        assert command.source == "chat_service"

    @pytest.mark.asyncio
    async def test_sets_thread_id_on_facts(self):
        """Test: Sets thread_id on each fact before creating command."""
        session_id = "thread-session-xyz"

        # Create a real Fact mock that we can check
        mock_fact = MagicMock()
        mock_fact.importance = 0.8
        mock_fact.confidence = 0.9
        mock_fact.thread_id = None

        self.service.fact_extractor.extract_facts = AsyncMock(return_value=[mock_fact])

        await self.service._extract_and_save_facts(
            session_id=session_id,
            user_message="Test",
            assistant_message="Response"
        )

        # The fact's thread_id should be set to session_id
        assert mock_fact.thread_id == session_id

    @pytest.mark.asyncio
    async def test_returns_facts_written_count_from_gate(self):
        """Test: Returns the facts_written count from WriteResult."""
        self.write_gate.execute = AsyncMock(return_value=MagicMock(
            success=True,
            facts_written=3,
            fact_ids=["f1", "f2", "f3"]
        ))

        result = await self.service._extract_and_save_facts(
            session_id="test-session",
            user_message="Info",
            assistant_message="Response"
        )

        assert result == 3


class TestExtractAndSaveFactsBackwardCompatibility:
    """Test backward compatibility when write_gate is not provided."""

    def setup_method(self):
        """Setup service WITHOUT write_gate."""
        self.agent_service = MagicMock()
        self.memory_service = MagicMock()

        # Mock the return value properly
        mock_saved_fact = MagicMock()
        mock_saved_fact.fact_id = "saved-fact-1"
        self.memory_service.add_facts = AsyncMock(return_value=[mock_saved_fact])

        self.service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=MagicMock(),
            web_search_service=MagicMock(),
            # NO write_gate - backward compatibility
        )

        self.service.memorisator_enabled = True

        mock_fact = MagicMock()
        mock_fact.importance = 0.8
        mock_fact.confidence = 0.9
        mock_fact.thread_id = None

        self.service.fact_extractor = MagicMock()
        self.service.fact_extractor.extract_facts = AsyncMock(return_value=[mock_fact])

    @pytest.mark.asyncio
    async def test_falls_back_to_direct_add_facts(self):
        """Test: Falls back to memory_service.add_facts when no gate."""
        await self.service._extract_and_save_facts(
            session_id="test-session",
            user_message="Hello",
            assistant_message="Hi"
        )

        # Should call add_facts directly
        self.memory_service.add_facts.assert_called_once()

    @pytest.mark.asyncio
    async def test_still_sets_thread_id_on_facts(self):
        """Test: Sets thread_id on facts even without gate."""
        session_id = "backward-compat-session"

        mock_fact = MagicMock()
        mock_fact.importance = 0.8
        mock_fact.confidence = 0.9
        mock_fact.thread_id = None

        self.service.fact_extractor.extract_facts = AsyncMock(return_value=[mock_fact])

        await self.service._extract_and_save_facts(
            session_id=session_id,
            user_message="Test",
            assistant_message="Response"
        )

        # thread_id should still be set
        assert mock_fact.thread_id == session_id


class TestExtractAndSaveFactsErrorHandling:
    """Test error handling with write gate."""

    def setup_method(self):
        """Setup service with mocks."""
        self.agent_service = MagicMock()
        self.memory_service = MagicMock()

        self.write_gate = MagicMock()

        self.service = EnhancedChatService(
            agent_service=self.agent_service,
            memory_service=self.memory_service,
            document_service=MagicMock(),
            web_search_service=MagicMock(),
            write_gate=self.write_gate
        )

        self.service.memorisator_enabled = True

        mock_fact = MagicMock()
        mock_fact.importance = 0.8
        mock_fact.confidence = 0.9
        mock_fact.thread_id = None

        self.service.fact_extractor = MagicMock()
        self.service.fact_extractor.extract_facts = AsyncMock(return_value=[mock_fact])

    @pytest.mark.asyncio
    async def test_handles_gate_failure_gracefully(self):
        """Test: Returns 0 when write gate fails."""
        self.write_gate.execute = AsyncMock(return_value=MagicMock(
            success=False,
            facts_written=0,
            error="Validation failed"
        ))

        result = await self.service._extract_and_save_facts(
            session_id="test-session",
            user_message="Hello",
            assistant_message="Hi"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_handles_gate_exception_gracefully(self):
        """Test: Returns 0 when write gate throws exception."""
        self.write_gate.execute = AsyncMock(side_effect=Exception("Gate error"))

        result = await self.service._extract_and_save_facts(
            session_id="test-session",
            user_message="Hello",
            assistant_message="Hi"
        )

        # Should not raise, should return 0
        assert result == 0