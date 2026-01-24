"""
Tests for clear_thread_facts method

Epic 1: Thread Isolation
Task 1.4: Implement session reset logic to clear thread working memory

Why this test exists:
- When user resets/deletes a session, all facts for that thread must be deleted
- Facts in OTHER threads must NOT be affected
- This enables proper session cleanup and privacy
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.memory_v2 import Fact, FactModel
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
async def populated_threads(memory_service):
    """
    Create facts in multiple threads for testing

    Thread A: "thread-alice" - 3 facts
    Thread B: "thread-bob" - 2 facts
    Global: thread_id=None - 1 fact
    """
    # Thread A - Alice's facts
    alice_facts = [
        Fact(fact_id="alice-1", text="Alice fact 1", thread_id="thread-alice", importance=0.9),
        Fact(fact_id="alice-2", text="Alice fact 2", thread_id="thread-alice", importance=0.8),
        Fact(fact_id="alice-3", text="Alice fact 3", thread_id="thread-alice", importance=0.7),
    ]

    # Thread B - Bob's facts
    bob_facts = [
        Fact(fact_id="bob-1", text="Bob fact 1", thread_id="thread-bob", importance=0.85),
        Fact(fact_id="bob-2", text="Bob fact 2", thread_id="thread-bob", importance=0.75),
    ]

    # Global facts
    global_facts = [
        Fact(fact_id="global-1", text="Global fact", thread_id=None, importance=0.8),
    ]

    await memory_service.add_facts(alice_facts)
    await memory_service.add_facts(bob_facts)
    await memory_service.add_facts(global_facts)

    return {
        "alice_count": len(alice_facts),
        "bob_count": len(bob_facts),
        "global_count": len(global_facts),
        "total": len(alice_facts) + len(bob_facts) + len(global_facts)
    }


class TestClearThreadFacts:
    """Test suite for clear_thread_facts method"""

    @pytest.mark.asyncio
    async def test_clear_thread_facts_deletes_all_thread_facts(
            self, memory_service, populated_threads
    ):
        """Test: clear_thread_facts deletes ALL facts for specified thread"""
        # Arrange - verify Alice has facts
        alice_facts = await memory_service.search_facts(
            query="Alice", thread_id="thread-alice"
        )
        assert len(alice_facts) == 3

        # Act - clear Alice's thread
        deleted_count = await memory_service.clear_thread_facts("thread-alice")

        # Assert - all Alice's facts deleted
        assert deleted_count == 3

        # Verify by searching
        alice_facts_after = await memory_service.search_facts(
            query="Alice", thread_id="thread-alice"
        )
        assert len(alice_facts_after) == 0

    @pytest.mark.asyncio
    async def test_clear_thread_facts_does_not_affect_other_threads(
            self, memory_service, populated_threads
    ):
        """Test: Clearing Thread A does NOT delete Thread B facts"""
        # Act - clear Alice's thread
        await memory_service.clear_thread_facts("thread-alice")

        # Assert - Bob's facts still exist
        bob_facts = await memory_service.search_facts(
            query="Bob", thread_id="thread-bob"
        )
        assert len(bob_facts) == 2, "Bob's facts must NOT be affected!"

    @pytest.mark.asyncio
    async def test_clear_thread_facts_does_not_affect_global_facts(
            self, memory_service, populated_threads
    ):
        """Test: Clearing a thread does NOT delete global facts (thread_id=None)"""
        # Act - clear Alice's thread
        await memory_service.clear_thread_facts("thread-alice")

        # Assert - global facts still exist
        global_facts = await memory_service.search_facts(
            query="Global", thread_id=None
        )
        assert len(global_facts) == 1, "Global facts must NOT be affected!"

    @pytest.mark.asyncio
    async def test_clear_thread_facts_returns_deleted_count(
            self, memory_service, populated_threads
    ):
        """Test: clear_thread_facts returns number of deleted facts"""
        # Act
        deleted_count = await memory_service.clear_thread_facts("thread-alice")

        # Assert
        assert deleted_count == 3  # Alice had 3 facts

    @pytest.mark.asyncio
    async def test_clear_thread_facts_empty_thread_returns_zero(
            self, memory_service, populated_threads
    ):
        """Test: Clearing non-existent thread returns 0"""
        # Act
        deleted_count = await memory_service.clear_thread_facts("thread-nonexistent")

        # Assert
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_clear_thread_facts_none_thread_id_clears_global(
            self, memory_service, populated_threads
    ):
        """Test: clear_thread_facts(None) clears global facts only"""
        # Act - clear global facts
        deleted_count = await memory_service.clear_thread_facts(None)

        # Assert - global fact deleted
        assert deleted_count == 1

        # Verify global facts gone
        global_facts = await memory_service.search_facts(query="Global", thread_id=None)
        assert len(global_facts) == 0

        # But thread-specific facts remain
        alice_facts = await memory_service.search_facts(query="Alice", thread_id="thread-alice")
        assert len(alice_facts) == 3


class TestClearThreadFactsEdgeCases:
    """Edge cases for clear_thread_facts"""

    @pytest.mark.asyncio
    async def test_clear_thread_facts_twice_is_safe(
            self, memory_service, populated_threads
    ):
        """Test: Calling clear twice on same thread is safe (idempotent)"""
        # Act - clear twice
        first_delete = await memory_service.clear_thread_facts("thread-alice")
        second_delete = await memory_service.clear_thread_facts("thread-alice")

        # Assert
        assert first_delete == 3
        assert second_delete == 0  # Already cleared

    @pytest.mark.asyncio
    async def test_clear_thread_facts_empty_database(self, memory_service):
        """Test: clear_thread_facts on empty database returns 0"""
        # Act - no facts exist
        deleted_count = await memory_service.clear_thread_facts("any-thread")

        # Assert
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_clear_thread_facts_preserves_database_integrity(
            self, memory_service, populated_threads
    ):
        """Test: After clearing, database operations still work"""
        # Act - clear a thread
        await memory_service.clear_thread_facts("thread-alice")

        # Assert - can still add new facts
        new_fact = Fact(
            fact_id="new-fact",
            text="New fact after clear",
            thread_id="thread-alice",
            importance=0.9
        )
        saved = await memory_service.add_facts([new_fact])

        assert len(saved) == 1
        assert saved[0].thread_id == "thread-alice"


class TestClearThreadFactsIntegration:
    """Integration tests for session reset workflow"""

    @pytest.mark.asyncio
    async def test_full_session_reset_workflow(self, memory_service):
        """Test: Complete workflow of creating session, adding facts, then resetting"""
        session_id = "session-to-reset"

        # Step 1: Create facts in session
        facts = [
            Fact(fact_id=f"sess-fact-{i}", text=f"Session fact {i}", thread_id=session_id)
            for i in range(5)
        ]
        await memory_service.add_facts(facts)

        # Verify facts exist
        session_facts = await memory_service.search_facts(query="Session", thread_id=session_id)
        assert len(session_facts) == 5

        # Step 2: Reset session (clear all facts)
        deleted = await memory_service.clear_thread_facts(session_id)
        assert deleted == 5

        # Step 3: Verify session is clean
        session_facts_after = await memory_service.search_facts(query="Session", thread_id=session_id)
        assert len(session_facts_after) == 0

        # Step 4: Can start fresh in same session
        new_fact = Fact(fact_id="fresh-start", text="Fresh start", thread_id=session_id)
        await memory_service.add_facts([new_fact])

        fresh_facts = await memory_service.search_facts(query="Fresh", thread_id=session_id)
        assert len(fresh_facts) == 1