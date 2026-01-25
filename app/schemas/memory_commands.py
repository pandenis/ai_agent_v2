"""
Memory Write Command Schema

Epic 2: Memory Write Centralization
Task 2.1: Create MemoryWriteCommand schema for write requests

This module defines the command pattern for all memory writes.
All memory modifications should go through MemoryWriteCommand to:
- Enforce thread_id on every write
- Track source of write requests
- Enable validation before execution
- Support queueing and prioritization
- Provide audit logging capability
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.memory_v2 import Fact


@dataclass
class MemoryWriteCommand:
    """
    Command object for centralized memory writes.

    All memory write operations should be wrapped in this command
    to ensure thread isolation, validation, and audit capability.

    Attributes:
        facts: List of Fact objects to write
        thread_id: Target thread for isolation (required)
        source: Origin of the write request (e.g., "orchestrator", "api")
        operation: Type of operation ("add", "update", "delete")
        priority: Processing priority (higher = first)
        created_at: Timestamp when command was created
        metadata: Additional context for auditing

    Example:
        >>> facts = [Fact(fact_id="f1", text="User likes Python", thread_id="session-123")]
        >>> cmd = MemoryWriteCommand(
        ...     facts=facts,
        ...     thread_id="session-123",
        ...     source="orchestrator"
        ... )
        >>> cmd.fact_count
        1
        >>> cmd.validate_thread_consistency()
        True
    """

    # Required fields
    facts: List[Fact]
    thread_id: str
    source: str

    # Optional fields with defaults
    operation: str = "add"
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate_thread_consistency(self) -> bool:
        """
        Validate that all facts have matching thread_id.

        Returns:
            True if all facts match command's thread_id or facts list is empty.
            False if any fact has mismatched thread_id.
        """
        if not self.facts:
            return True

        return all(
            fact.thread_id == self.thread_id
            for fact in self.facts
        )

    @property
    def fact_count(self) -> int:
        """Return the number of facts in this command."""
        return len(self.facts)

    @property
    def fact_ids(self) -> List[str]:
        """Return list of fact IDs in this command."""
        return [fact.fact_id for fact in self.facts]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert command to dictionary for serialization/logging.

        Returns:
            Dictionary representation of the command (excludes full fact objects).
        """
        return {
            "thread_id": self.thread_id,
            "source": self.source,
            "operation": self.operation,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "fact_count": self.fact_count,
            "fact_ids": self.fact_ids,
            "metadata": self.metadata,
        }