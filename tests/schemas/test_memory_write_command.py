"""
Tests for MemoryWriteCommand schema

Epic 2: Memory Write Centralization
Task 2.1: Create MemoryWriteCommand schema for write requests

Why this exists:
- All memory writes should go through a centralized command pattern
- Commands capture: what to write, where (thread), who requested, and operation type
- Enables validation, queueing, and audit logging of all writes
"""
import pytest
from datetime import datetime
from typing import List

from app.models.memory_v2 import Fact


class TestMemoryWriteCommandCreation:
    """Test MemoryWriteCommand creation and defaults."""

    def test_create_command_with_required_fields(self):
        """Test: Create command with minimum required fields."""
        from app.schemas.memory_commands import MemoryWriteCommand

        facts = [
            Fact(fact_id="test-1", text="Test fact", thread_id="thread-123")
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-123",
            source="orchestrator"
        )

        assert command.facts == facts
        assert command.thread_id == "thread-123"
        assert command.source == "orchestrator"
        assert command.operation == "add"  # Default

    def test_create_command_with_all_fields(self):
        """Test: Create command with all fields specified."""
        from app.schemas.memory_commands import MemoryWriteCommand

        facts = [Fact(fact_id="f1", text="Fact 1", thread_id="thread-abc")]
        created = datetime(2026, 1, 25, 12, 0, 0)

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-abc",
            source="api",
            operation="add",
            priority=10,
            created_at=created,
            metadata={"session_id": "sess-123", "user_id": "user-456"}
        )

        assert command.facts == facts
        assert command.thread_id == "thread-abc"
        assert command.source == "api"
        assert command.operation == "add"
        assert command.priority == 10
        assert command.created_at == created
        assert command.metadata == {"session_id": "sess-123", "user_id": "user-456"}

    def test_command_default_values(self):
        """Test: Command has sensible defaults."""
        from app.schemas.memory_commands import MemoryWriteCommand

        command = MemoryWriteCommand(
            facts=[],
            thread_id="thread-default",
            source="test"
        )

        assert command.operation == "add"
        assert command.priority == 0
        assert command.metadata == {}
        assert isinstance(command.created_at, datetime)

    def test_command_with_multiple_facts(self):
        """Test: Command can hold multiple facts."""
        from app.schemas.memory_commands import MemoryWriteCommand

        facts = [
            Fact(fact_id=f"fact-{i}", text=f"Fact {i}", thread_id="thread-multi")
            for i in range(10)
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-multi",
            source="bulk_import"
        )

        assert len(command.facts) == 10


class TestMemoryWriteCommandOperations:
    """Test different operation types."""

    def test_add_operation(self):
        """Test: 'add' operation for new facts."""
        from app.schemas.memory_commands import MemoryWriteCommand

        command = MemoryWriteCommand(
            facts=[Fact(fact_id="new-1", text="New fact", thread_id="t1")],
            thread_id="t1",
            source="orchestrator",
            operation="add"
        )

        assert command.operation == "add"

    def test_update_operation(self):
        """Test: 'update' operation for existing facts."""
        from app.schemas.memory_commands import MemoryWriteCommand

        command = MemoryWriteCommand(
            facts=[Fact(fact_id="existing-1", text="Updated text", thread_id="t1")],
            thread_id="t1",
            source="orchestrator",
            operation="update"
        )

        assert command.operation == "update"

    def test_delete_operation(self):
        """Test: 'delete' operation for removing facts."""
        from app.schemas.memory_commands import MemoryWriteCommand

        command = MemoryWriteCommand(
            facts=[Fact(fact_id="to-delete", text="", thread_id="t1")],
            thread_id="t1",
            source="orchestrator",
            operation="delete"
        )

        assert command.operation == "delete"


class TestMemoryWriteCommandValidation:
    """Test command validation."""

    def test_thread_id_must_match_facts(self):
        """Test: Command thread_id should match facts' thread_id."""
        from app.schemas.memory_commands import MemoryWriteCommand

        # Facts with matching thread_id
        facts = [
            Fact(fact_id="f1", text="Fact 1", thread_id="thread-match"),
            Fact(fact_id="f2", text="Fact 2", thread_id="thread-match"),
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-match",
            source="test"
        )

        assert command.validate_thread_consistency() is True

    def test_thread_id_mismatch_detected(self):
        """Test: Detect when fact thread_id doesn't match command thread_id."""
        from app.schemas.memory_commands import MemoryWriteCommand

        # Facts with mismatched thread_id
        facts = [
            Fact(fact_id="f1", text="Fact 1", thread_id="thread-A"),
            Fact(fact_id="f2", text="Fact 2", thread_id="thread-B"),  # Mismatch!
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="thread-A",
            source="test"
        )

        assert command.validate_thread_consistency() is False

    def test_empty_facts_allowed(self):
        """Test: Empty facts list is allowed (for delete operations)."""
        from app.schemas.memory_commands import MemoryWriteCommand

        command = MemoryWriteCommand(
            facts=[],
            thread_id="thread-empty",
            source="test",
            operation="delete"
        )

        assert len(command.facts) == 0
        assert command.validate_thread_consistency() is True


class TestMemoryWriteCommandHelpers:
    """Test helper methods."""

    def test_fact_count(self):
        """Test: fact_count property returns correct count."""
        from app.schemas.memory_commands import MemoryWriteCommand

        facts = [
            Fact(fact_id=f"f{i}", text=f"Fact {i}", thread_id="t1")
            for i in range(5)
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="t1",
            source="test"
        )

        assert command.fact_count == 5

    def test_fact_ids_property(self):
        """Test: fact_ids property returns list of fact IDs."""
        from app.schemas.memory_commands import MemoryWriteCommand

        facts = [
            Fact(fact_id="alpha", text="Alpha", thread_id="t1"),
            Fact(fact_id="beta", text="Beta", thread_id="t1"),
            Fact(fact_id="gamma", text="Gamma", thread_id="t1"),
        ]

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="t1",
            source="test"
        )

        assert command.fact_ids == ["alpha", "beta", "gamma"]

    def test_to_dict(self):
        """Test: to_dict method for serialization."""
        from app.schemas.memory_commands import MemoryWriteCommand

        facts = [Fact(fact_id="f1", text="Test", thread_id="t1")]
        created = datetime(2026, 1, 25, 12, 0, 0)

        command = MemoryWriteCommand(
            facts=facts,
            thread_id="t1",
            source="api",
            operation="add",
            priority=5,
            created_at=created,
            metadata={"key": "value"}
        )

        d = command.to_dict()

        assert d["thread_id"] == "t1"
        assert d["source"] == "api"
        assert d["operation"] == "add"
        assert d["priority"] == 5
        assert d["fact_count"] == 1
        assert d["fact_ids"] == ["f1"]
        assert d["metadata"] == {"key": "value"}
        assert "created_at" in d