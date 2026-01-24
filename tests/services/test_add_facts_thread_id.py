"""
Tests for add_facts thread_id support

Epic 1: Thread Isolation
Task 1.3: Update add_facts to require thread_id on all writes

Why this test exists:
- Facts must be saved with thread_id for isolation
- Current behavior: add_facts ignores thread_id from Fact dataclass
- Required: thread_id must be passed through and saved
"""
import pytest
from datetime import datetime
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


class TestAddFactsThreadId:
    """Test suite for add_facts thread_id support"""

    @pytest.mark.asyncio
    async def test_add_facts_saves_thread_id(self, memory_service):
        """Test: add_facts saves thread_id from Fact dataclass to database"""
        # Arrange
        fact = Fact(
            fact_id="test-fact-001",
            text="User prefers morning meetings",
            thread_id="thread-session-abc",  # Thread ID set
            importance=0.8,
            confidence=0.9,
            fact_type="preference",
            source="conversation"
        )

        # Act
        saved_facts = await memory_service.add_facts([fact])

        # Assert
        assert len(saved_facts) == 1
        assert saved_facts[0].thread_id == "thread-session-abc", \
            "thread_id must be saved to database"

    @pytest.mark.asyncio
    async def test_add_facts_multiple_with_different_threads(self, memory_service):
        """Test: add_facts saves multiple facts with different thread_ids"""
        # Arrange - facts from two different threads
        facts = [
            Fact(
                fact_id="alice-fact-1",
                text="Alice likes Python",
                thread_id="thread-alice",
                importance=0.9
            ),
            Fact(
                fact_id="bob-fact-1",
                text="Bob likes cooking",
                thread_id="thread-bob",
                importance=0.85
            ),
        ]

        # Act
        saved_facts = await memory_service.add_facts(facts)

        # Assert
        assert len(saved_facts) == 2
        thread_ids = {f.thread_id for f in saved_facts}
        assert thread_ids == {"thread-alice", "thread-bob"}, \
            "Each fact should preserve its own thread_id"

    @pytest.mark.asyncio
    async def test_add_facts_with_none_thread_id_allowed(self, memory_service):
        """Test: add_facts allows None thread_id for backward compatibility"""
        # Arrange - fact without thread_id (legacy behavior)
        fact = Fact(
            fact_id="legacy-fact-001",
            text="Legacy fact without thread",
            thread_id=None,  # No thread (global fact)
            importance=0.7
        )

        # Act
        saved_facts = await memory_service.add_facts([fact])

        # Assert - should save without error
        assert len(saved_facts) == 1
        assert saved_facts[0].thread_id is None

    @pytest.mark.asyncio
    async def test_add_facts_retrieval_respects_thread_id(self, memory_service):
        """Test: Facts added with thread_id can be retrieved with isolation"""
        # Arrange - add facts to different threads
        alice_fact = Fact(
            fact_id="alice-isolated-1",
            text="Alice secret preference",
            thread_id="thread-alice-private",
            importance=0.9
        )
        bob_fact = Fact(
            fact_id="bob-isolated-1",
            text="Bob secret preference",
            thread_id="thread-bob-private",
            importance=0.9
        )

        await memory_service.add_facts([alice_fact, bob_fact])

        # Act - search in Alice's thread
        alice_results = await memory_service.search_facts(
            query="secret",
            thread_id="thread-alice-private"
        )

        # Assert - only Alice's fact found
        assert len(alice_results) == 1
        assert alice_results[0].fact_id == "alice-isolated-1"
        assert alice_results[0].thread_id == "thread-alice-private"

    @pytest.mark.asyncio
    async def test_add_facts_no_cross_thread_pollution(self, memory_service):
        """Test: Facts from one thread NEVER appear in another thread's search"""
        # Arrange - add fact to Alice's thread
        alice_fact = Fact(
            fact_id="alice-only-fact",
            text="This is Alice only data",
            thread_id="thread-alice-only",
            importance=0.95
        )
        await memory_service.add_facts([alice_fact])

        # Act - search in Bob's thread (different thread)
        bob_results = await memory_service.search_facts(
            query="Alice",
            thread_id="thread-bob-different"
        )

        # Assert - Bob should NOT see Alice's facts
        assert len(bob_results) == 0, \
            "Alice's facts must NOT appear in Bob's thread search!"


class TestAddFactsThreadIdEdgeCases:
    """Edge cases for thread_id in add_facts"""

    @pytest.mark.asyncio
    async def test_add_facts_empty_list(self, memory_service):
        """Test: add_facts with empty list returns empty list"""
        # Act
        result = await memory_service.add_facts([])

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_add_facts_same_thread_multiple_facts(self, memory_service):
        """Test: Multiple facts with same thread_id are all saved correctly"""
        # Arrange
        facts = [
            Fact(fact_id=f"same-thread-{i}", text=f"Fact {i}", thread_id="shared-thread")
            for i in range(5)
        ]

        # Act
        saved = await memory_service.add_facts(facts)

        # Assert
        assert len(saved) == 5
        assert all(f.thread_id == "shared-thread" for f in saved)

    @pytest.mark.asyncio
    async def test_add_facts_mixed_thread_and_none(self, memory_service):
        """Test: Can add mix of thread-specific and global facts"""
        # Arrange
        facts = [
            Fact(fact_id="with-thread", text="Has thread", thread_id="my-thread"),
            Fact(fact_id="without-thread", text="No thread", thread_id=None),
        ]

        # Act
        saved = await memory_service.add_facts(facts)

        # Assert
        assert len(saved) == 2
        thread_ids = {f.fact_id: f.thread_id for f in saved}
        assert thread_ids["with-thread"] == "my-thread"
        assert thread_ids["without-thread"] is None


class TestAddFactsIntegrationWithSearch:
    """Integration tests: add_facts + search_facts thread isolation"""

    @pytest.mark.asyncio
    async def test_full_isolation_workflow(self, memory_service):
        """Test: Complete workflow of adding and searching with thread isolation"""
        # === SETUP: Create facts in 3 different contexts ===

        # Thread 1: Work conversation
        work_facts = [
            Fact(fact_id="work-1", text="Project deadline is Friday", thread_id="work-thread"),
            Fact(fact_id="work-2", text="Meeting with team at 2pm", thread_id="work-thread"),
        ]

        # Thread 2: Personal conversation
        personal_facts = [
            Fact(fact_id="personal-1", text="Doctor appointment Friday", thread_id="personal-thread"),
            Fact(fact_id="personal-2", text="Buy groceries", thread_id="personal-thread"),
        ]

        # Global facts (no thread)
        global_facts = [
            Fact(fact_id="global-1", text="User lives in Tel Aviv", thread_id=None),
        ]

        # Add all facts
        await memory_service.add_facts(work_facts)
        await memory_service.add_facts(personal_facts)
        await memory_service.add_facts(global_facts)

        # === TEST: Search in work thread ===
        work_results = await memory_service.search_facts(
            query="Friday",
            thread_id="work-thread"
        )

        # Should find work deadline, NOT personal appointment
        assert len(work_results) == 1
        assert work_results[0].fact_id == "work-1"
        assert "deadline" in work_results[0].text

        # === TEST: Search in personal thread ===
        personal_results = await memory_service.search_facts(
            query="Friday",
            thread_id="personal-thread"
        )

        # Should find doctor appointment, NOT work deadline
        assert len(personal_results) == 1
        assert personal_results[0].fact_id == "personal-1"
        assert "Doctor" in personal_results[0].text

        # === TEST: Search global facts ===
        global_results = await memory_service.search_facts(
            query="Tel Aviv",
            thread_id=None
        )

        # Should find global fact
        assert len(global_results) == 1
        assert global_results[0].fact_id == "global-1"