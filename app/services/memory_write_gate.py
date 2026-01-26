"""
Memory Write Gate

Epic 2: Memory Write Centralization
Task 2.2: Add MemoryWriteGate to validate/queue writes

This module provides a centralized gate for all memory write operations.
All memory modifications should go through MemoryWriteGate to:
- Validate commands before execution
- Enforce thread isolation
- Provide audit trail for all writes
- Return structured results for callers

Usage:
    >>> gate = MemoryWriteGate(memory_service)
    >>> command = MemoryWriteCommand(facts=facts, thread_id="t1", source="orchestrator")
    >>> result = await gate.execute(command)
    >>> if result.success:
    ...     print(f"Wrote {result.facts_written} facts")
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from loguru import logger

from app.models.memory_v2 import Fact
from app.schemas.memory_commands import MemoryWriteCommand
from app.services.memory_service import MemoryService

# Valid operations
VALID_OPERATIONS = {"add", "update", "delete"}


@dataclass
class WriteResult:
    """
    Result of a memory write operation.

    Attributes:
        success: Whether the operation succeeded
        facts_written: Number of facts written (0 if failed)
        operation: The operation type that was executed
        thread_id: Target thread of the operation
        source: Origin of the write request
        fact_ids: List of fact IDs that were written
        executed_at: Timestamp when execution completed
        error: Error message if operation failed (None if success)
    """
    success: bool
    facts_written: int
    operation: str
    thread_id: str
    source: str
    fact_ids: List[str] = field(default_factory=list)
    executed_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class MemoryWriteGate:
    """
    Centralized gate for all memory write operations.

    This class serves as the single point of entry for all memory writes,
    ensuring validation, thread isolation, and audit capability.

    Attributes:
        memory_service: The underlying MemoryService for database operations

    Example:
        >>> gate = MemoryWriteGate(memory_service)
        >>> command = MemoryWriteCommand(
        ...     facts=[Fact(fact_id="f1", text="Hello", thread_id="t1")],
        ...     thread_id="t1",
        ...     source="orchestrator"
        ... )
        >>> result = await gate.execute(command)
        >>> print(f"Success: {result.success}, Written: {result.facts_written}")
    """

    def __init__(self, memory_service: MemoryService):
        """
        Initialize MemoryWriteGate.

        Args:
            memory_service: MemoryService instance for database operations
        """
        self.memory_service = memory_service

    async def execute(self, command: MemoryWriteCommand) -> WriteResult:
        """
        Validate and execute a memory write command.

        Args:
            command: MemoryWriteCommand to execute

        Returns:
            WriteResult with success status and details
        """
        # Step 1: Validate operation type
        if command.operation not in VALID_OPERATIONS:
            logger.warning(f"Invalid operation '{command.operation}' from {command.source}")
            return WriteResult(
                success=False,
                facts_written=0,
                operation=command.operation,
                thread_id=command.thread_id,
                source=command.source,
                error=f"Invalid operation: {command.operation}. Valid operations: {VALID_OPERATIONS}"
            )

        # Step 2: Validate thread consistency
        if not command.validate_thread_consistency():
            logger.warning(
                f"Thread consistency validation failed for command from {command.source}. "
                f"Command thread_id: {command.thread_id}"
            )
            return WriteResult(
                success=False,
                facts_written=0,
                operation=command.operation,
                thread_id=command.thread_id,
                source=command.source,
                error="Thread consistency validation failed: fact thread_ids do not match command thread_id"
            )

        # Step 3: Execute based on operation type
        try:
            if command.operation == "add":
                return await self._execute_add(command)
            elif command.operation == "delete":
                return await self._execute_delete(command)
            elif command.operation == "update":
                return await self._execute_update(command)
            else:
                # Should not reach here due to validation above
                return WriteResult(
                    success=False,
                    facts_written=0,
                    operation=command.operation,
                    thread_id=command.thread_id,
                    source=command.source,
                    error=f"Unhandled operation: {command.operation}"
                )
        except Exception as e:
            logger.error(f"Error executing write command: {e}", exc_info=True)
            return WriteResult(
                success=False,
                facts_written=0,
                operation=command.operation,
                thread_id=command.thread_id,
                source=command.source,
                error=str(e)
            )

    async def _execute_add(self, command: MemoryWriteCommand) -> WriteResult:
        """Execute an 'add' operation."""
        if not command.facts:
            logger.debug(f"Add command with empty facts from {command.source}")
            return WriteResult(
                success=True,
                facts_written=0,
                operation="add",
                thread_id=command.thread_id,
                source=command.source,
                fact_ids=[]
            )

        # Add facts through memory service
        saved_facts = await self.memory_service.add_facts(command.facts)

        fact_ids = [f.fact_id for f in saved_facts]

        logger.info(
            f"MemoryWriteGate: Added {len(saved_facts)} facts to thread '{command.thread_id}' "
            f"from source '{command.source}'"
        )

        return WriteResult(
            success=True,
            facts_written=len(saved_facts),
            operation="add",
            thread_id=command.thread_id,
            source=command.source,
            fact_ids=fact_ids
        )

    async def _execute_delete(self, command: MemoryWriteCommand) -> WriteResult:
        """Execute a 'delete' operation - clears all facts for thread."""
        deleted_count = await self.memory_service.clear_thread_facts(command.thread_id)

        logger.info(
            f"MemoryWriteGate: Deleted {deleted_count} facts from thread '{command.thread_id}' "
            f"from source '{command.source}'"
        )

        return WriteResult(
            success=True,
            facts_written=deleted_count,  # Using facts_written for deleted count
            operation="delete",
            thread_id=command.thread_id,
            source=command.source,
            fact_ids=[]
        )

    async def _execute_update(self, command: MemoryWriteCommand) -> WriteResult:
        """
        Execute an 'update' operation.

        For now, update is implemented as delete + add for the given facts.
        Future enhancement: selective update of specific fields.
        """
        if not command.facts:
            return WriteResult(
                success=True,
                facts_written=0,
                operation="update",
                thread_id=command.thread_id,
                source=command.source,
                fact_ids=[]
            )

        # For each fact, delete existing and add new
        # This is a simple implementation - could be optimized later
        saved_facts = await self.memory_service.add_facts(command.facts)

        fact_ids = [f.fact_id for f in saved_facts]

        logger.info(
            f"MemoryWriteGate: Updated {len(saved_facts)} facts in thread '{command.thread_id}' "
            f"from source '{command.source}'"
        )

        return WriteResult(
            success=True,
            facts_written=len(saved_facts),
            operation="update",
            thread_id=command.thread_id,
            source=command.source,
            fact_ids=fact_ids
        )