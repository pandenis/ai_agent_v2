"""
Tests for MemoryWriteGate

Epic 2: Memory Write Centralization
Task 2.2: Add MemoryWriteGate to validate/queue writes

Why this exists:
- Single point of entry for all memory writes
- Validates commands before execution
- Enforces thread isolation
- Provides audit trail for all writes
- Returns structured results for callers
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.memory_v2 import Fact, FactModel
from app.schemas.memory_commands import MemoryWriteCommand
from app.services.memory_service import MemoryService

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def memory_service(test_session):
    """Create MemoryService with test session"""
    return MemoryService(test_session)


@pytest.fixture
async def write_gate(memory_service):
    """Create MemoryWriteGate with memory service"""
    from app.services.memory_write_gate import MemoryWriteGate
    return MemoryWriteGate(memory_service)


class TestMemoryWriteGateCreation:
    """Test MemoryWriteGate instantiation."""

    def test_create_write_gate(self, memory_service):
        """Test: Create MemoryWriteGate with memory service."""
        from app.services.memory_write_gate import MemoryWriteGate

        gate = MemoryWriteGate(memory_service)

        assert gate.memory_service == memory_service

    def test_write_gate_has_execute_method(self, memory_service):
        """Test: MemoryWriteGate has execute method."""
        from app.services.memory_write_gate import MemoryWriteGate

        gate = MemoryWriteGate(memory_service)

        assert hasattr(gate, 'execute')
        assert callable(gate.execute)


class TestMemoryWriteGateExecute:
    """Test MemoryWriteGate.execute() method."""

    @pytest.mark.asyncio
    async def test_execute_add_operation_saves_facts(self, write_gate, memory_service):
        """Test: Execute 'add' operation saves facts to database."""
        facts = [
            Fact(fact_id="gate-fact-1", text="Fact from gate", thread_id="thread-gate", importance=0.8),
            Fact(fact_id="gate-fact-2", text="Another gate fact", thread_id="thread-gate", importance=0.7),
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-gate",
            source="orchestrator",
            operation="add"
        )

        # Execute
        result = await write_gate.execute(command)

        # Verify result
        assert result.success is True
        assert result.facts_written == 2
        assert result.operation == "add"

        # Verify facts are in database
        saved = await memory_service.search_facts(query="gate", thread_id="thread-gate", limit=10)
        assert len(saved) == 2

    @pytest.mark.asyncio
    async def test_execute_returns_write_result(self, write_gate):
        """Test: Execute returns a WriteResult object."""
        from app.services.memory_write_gate import WriteResult

        command = MemoryWriteCommand(
            facts=[Fact(fact_id="f1", text="Test", thread_id="t1")],
            thread_id="t1",
            source="test"
        )

        result = await write_gate.execute(command)

        assert isinstance(result, WriteResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'facts_written')
        assert hasattr(result, 'operation')
        assert hasattr(result, 'thread_id')
        assert hasattr(result, 'error')

    @pytest.mark.asyncio
    async def test_execute_with_empty_facts(self, write_gate):
        """Test: Execute with empty facts list succeeds with 0 written."""
        command = MemoryWriteCommand(
            facts=[],
            thread_id="thread-empty",
            source="test",
            operation="add"
        )

        result = await write_gate.execute(command)

        assert result.success is True
        assert result.facts_written == 0


class TestMemoryWriteGateValidation:
    """Test command validation in MemoryWriteGate."""

    @pytest.mark.asyncio
    async def test_execute_validates_thread_consistency(self, write_gate):
        """Test: Execute rejects commands with mismatched thread_ids."""
        # Facts have different thread_id than command
        facts = [
            Fact(fact_id="f1", text="Fact 1", thread_id="thread-A"),
            Fact(fact_id="f2", text="Fact 2", thread_id="thread-B"),  # Mismatch!
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-A",
            source="test"
        )

        result = await write_gate.execute(command)

        assert result.success is False
        assert "thread" in result.error.lower()
        assert result.facts_written == 0

    @pytest.mark.asyncio
    async def test_execute_rejects_invalid_operation(self, write_gate):
        """Test: Execute rejects unknown operation types."""
        command = MemoryWriteCommand(
            facts=[Fact(fact_id="f1", text="Test", thread_id="t1")],
            thread_id="t1",
            source="test",
            operation="invalid_op"
        )

        result = await write_gate.execute(command)

        assert result.success is False
        assert "operation" in result.error.lower()


class TestMemoryWriteGateOperations:
    """Test different operation types."""

    @pytest.mark.asyncio
    async def test_delete_operation_clears_thread(self, write_gate, memory_service):
        """Test: 'delete' operation clears facts for thread."""
        thread_id = "thread-to-delete"

        # First add some facts
        facts = [
            Fact(fact_id=f"del-{i}", text=f"Delete me {i}", thread_id=thread_id)
            for i in range(3)
        ]
        await memory_service.add_facts(facts)

        # Verify facts exist
        before = await memory_service.search_facts(query="Delete", thread_id=thread_id, limit=10)
        assert len(before) == 3

        # Execute delete command
        command = MemoryWriteCommand(
            facts=[],  # Empty for delete
            thread_id=thread_id,
            source="test",
            operation="delete"
        )

        result = await write_gate.execute(command)

        assert result.success is True
        assert result.operation == "delete"

        # Verify facts are deleted
        after = await memory_service.search_facts(query="Delete", thread_id=thread_id, limit=10)
        assert len(after) == 0


class TestMemoryWriteGateAudit:
    """Test audit/logging capabilities."""

    @pytest.mark.asyncio
    async def test_write_result_includes_timestamp(self, write_gate):
        """Test: WriteResult includes execution timestamp."""
        command = MemoryWriteCommand(
            facts=[Fact(fact_id="f1", text="Test", thread_id="t1")],
            thread_id="t1",
            source="test"
        )

        result = await write_gate.execute(command)

        assert hasattr(result, 'executed_at')
        assert isinstance(result.executed_at, datetime)

    @pytest.mark.asyncio
    async def test_write_result_includes_source(self, write_gate):
        """Test: WriteResult includes original source."""
        command = MemoryWriteCommand(
            facts=[Fact(fact_id="f1", text="Test", thread_id="t1")],
            thread_id="t1",
            source="orchestrator"
        )

        result = await write_gate.execute(command)

        assert result.source == "orchestrator"

    @pytest.mark.asyncio
    async def test_write_result_includes_fact_ids(self, write_gate):
        """Test: WriteResult includes IDs of written facts."""
        facts = [
            Fact(fact_id="audit-1", text="Fact 1", thread_id="t1"),
            Fact(fact_id="audit-2", text="Fact 2", thread_id="t1"),
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="t1",
            source="test"
        )

        result = await write_gate.execute(command)

        assert result.fact_ids == ["audit-1", "audit-2"]


class TestMemoryWriteGateIntegration:
    """Integration tests for MemoryWriteGate."""

    @pytest.mark.asyncio
    async def test_full_write_workflow(self, write_gate, memory_service):
        """Test: Complete workflow from command to searchable facts."""
        thread_id = "integration-thread"

        # Create command
        facts = [
            Fact(fact_id="int-1", text="Integration test fact one", thread_id=thread_id, importance=0.9),
            Fact(fact_id="int-2", text="Integration test fact two", thread_id=thread_id, importance=0.8),
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id=thread_id,
            source="integration_test",
            metadata={"test_run": "workflow"}
        )

        # Execute through gate
        result = await write_gate.execute(command)

        # Verify success
        assert result.success is True
        assert result.facts_written == 2
        assert result.thread_id == thread_id
        assert result.source == "integration_test"

        # Verify facts are searchable
        found = await memory_service.search_facts(
            query="Integration",
            thread_id=thread_id,
            limit=10
        )
        assert len(found) == 2

        # Verify thread isolation
        other_thread = await memory_service.search_facts(
            query="Integration",
            thread_id="other-thread",
            limit=10
        )
        assert len(other_thread) == 0

    @pytest.mark.asyncio
    async def test_multiple_commands_same_thread(self, write_gate, memory_service):
        """Test: Multiple commands to same thread accumulate facts."""
        thread_id = "accumulate-thread"

        # First command
        cmd1 = MemoryWriteCommand(
            facts=[Fact(fact_id="acc-1", text="First batch", thread_id=thread_id)],
            thread_id=thread_id,
            source="test"
        )
        await write_gate.execute(cmd1)

        # Second command
        cmd2 = MemoryWriteCommand(
            facts=[Fact(fact_id="acc-2", text="Second batch", thread_id=thread_id)],
            thread_id=thread_id,
            source="test"
        )
        await write_gate.execute(cmd2)

        # Verify both facts exist
        found = await memory_service.search_facts(query="batch", thread_id=thread_id, limit=10)
        assert len(found) == 2