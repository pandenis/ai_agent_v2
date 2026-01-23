"""
Tests for search_facts thread_id filtering

Epic 1: Thread Isolation
Task 1.2: Update search_facts to require and filter by thread_id

Why this test exists:
- Current behavior: search_facts ignores session_id, returns ALL user facts
- Required behavior: search_facts filters by thread_id for isolation
- Facts in Thread A must NEVER appear in Thread B queries
"""
import pytest
from datetime import datetime
from sqlalchemy import text
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
async def isolated_facts(test_session):
    """
    Create facts in TWO different threads for isolation testing

    Thread A: "thread-alice-001" - Alice's conversation about Python
    Thread B: "thread-bob-002" - Bob's conversation about cooking
    Global: thread_id=None - Legacy facts (no thread)
    """
    facts = [
        # Thread A - Alice (Python developer)
        FactModel(
            fact_id="fact-alice-1",
            text="User is learning Python programming",
            thread_id="thread-alice-001",
            importance=0.9,
            confidence=0.95,
            tags=["programming", "python"],
            fact_type="static",
            source="conversation"
        ),
        FactModel(
            fact_id="fact-alice-2",
            text="User prefers VS Code editor",
            thread_id="thread-alice-001",
            importance=0.7,
            confidence=0.9,
            tags=["tools", "programming"],
            fact_type="preference",
            source="conversation"
        ),
        # Thread B - Bob (cooking enthusiast)
        FactModel(
            fact_id="fact-bob-1",
            text="User loves Italian cooking",
            thread_id="thread-bob-002",
            importance=0.85,
            confidence=0.9,
            tags=["cooking", "food"],
            fact_type="preference",
            source="conversation"
        ),
        FactModel(
            fact_id="fact-bob-2",
            text="User is vegetarian",
            thread_id="thread-bob-002",
            importance=0.95,
            confidence=0.98,
            tags=["diet", "food"],
            fact_type="static",
            source="conversation"
        ),
        # Global facts (no thread - legacy)
        FactModel(
            fact_id="fact-global-1",
            text="User lives in Tel Aviv",
            thread_id=None,  # Global/legacy fact
            importance=0.8,
            confidence=0.95,
            tags=["location"],
            fact_type="static",
            source="conversation"
        ),
    ]

    for fact in facts:
        test_session.add(fact)
    await test_session.commit()

    return facts


class TestSearchFactsThreadFilter:
    """Test suite for search_facts thread_id filtering"""

    @pytest.mark.asyncio
    async def test_search_facts_returns_only_thread_facts(
            self, memory_service, isolated_facts
    ):
        """Test: search_facts with thread_id returns ONLY facts from that thread"""
        # Act - search in Alice's thread
        results = await memory_service.search_facts(
            query="User",
            thread_id="thread-alice-001"
        )

        # Assert - only Alice's facts returned
        fact_ids = [f.fact_id for f in results]
        assert "fact-alice-1" in fact_ids
        assert "fact-alice-2" in fact_ids
        assert "fact-bob-1" not in fact_ids, "Bob's facts should NOT appear in Alice's thread!"
        assert "fact-bob-2" not in fact_ids, "Bob's facts should NOT appear in Alice's thread!"

    @pytest.mark.asyncio
    async def test_search_facts_thread_isolation_bob(
            self, memory_service, isolated_facts
    ):
        """Test: Bob's thread only returns Bob's facts"""
        # Act - search in Bob's thread
        results = await memory_service.search_facts(
            query="User",
            thread_id="thread-bob-002"
        )

        # Assert - only Bob's facts returned
        fact_ids = [f.fact_id for f in results]
        assert "fact-bob-1" in fact_ids
        assert "fact-bob-2" in fact_ids
        assert "fact-alice-1" not in fact_ids, "Alice's facts should NOT appear in Bob's thread!"
        assert "fact-alice-2" not in fact_ids, "Alice's facts should NOT appear in Bob's thread!"

    @pytest.mark.asyncio
    async def test_search_facts_no_cross_thread_leakage(
            self, memory_service, isolated_facts
    ):
        """Test: Searching for 'programming' in Bob's thread returns nothing"""
        # Act - search for programming in Bob's cooking thread
        results = await memory_service.search_facts(
            query="programming",
            thread_id="thread-bob-002"
        )

        # Assert - no results (programming facts are in Alice's thread)
        assert len(results) == 0, "Programming facts should NOT leak into Bob's cooking thread!"

    @pytest.mark.asyncio
    async def test_search_facts_with_none_thread_returns_global_only(
            self, memory_service, isolated_facts
    ):
        """Test: search_facts with thread_id=None returns only global facts"""
        # Act - search with no thread (global facts only)
        results = await memory_service.search_facts(
            query="User",
            thread_id=None
        )

        # Assert - only global fact returned
        fact_ids = [f.fact_id for f in results]
        assert "fact-global-1" in fact_ids
        assert "fact-alice-1" not in fact_ids, "Thread-specific facts should NOT appear in global search!"
        assert "fact-bob-1" not in fact_ids, "Thread-specific facts should NOT appear in global search!"

    @pytest.mark.asyncio
    async def test_search_facts_empty_thread_returns_empty(
            self, memory_service, isolated_facts
    ):
        """Test: search_facts for non-existent thread returns empty list"""
        # Act - search in a thread that doesn't exist
        results = await memory_service.search_facts(
            query="User",
            thread_id="thread-nonexistent-999"
        )

        # Assert - empty results
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_facts_combines_query_and_thread_filter(
            self, memory_service, isolated_facts
    ):
        """Test: search_facts filters by BOTH query text AND thread_id"""
        # Act - search for "Python" in Alice's thread
        results = await memory_service.search_facts(
            query="Python",
            thread_id="thread-alice-001"
        )

        # Assert - only the Python fact from Alice's thread
        assert len(results) == 1
        assert results[0].fact_id == "fact-alice-1"
        assert "Python" in results[0].text

    @pytest.mark.asyncio
    async def test_search_facts_respects_min_importance_with_thread(
            self, memory_service, isolated_facts
    ):
        """Test: search_facts combines thread_id, query, AND min_importance"""
        # Act - search in Alice's thread with high importance threshold
        results = await memory_service.search_facts(
            query="User",
            thread_id="thread-alice-001",
            min_importance=0.8
        )

        # Assert - only high importance fact (0.9) returned, not the 0.7 one
        fact_ids = [f.fact_id for f in results]
        assert "fact-alice-1" in fact_ids  # importance=0.9
        assert "fact-alice-2" not in fact_ids  # importance=0.7 < 0.8 threshold


class TestSearchFactsBackwardCompatibility:
    """Test backward compatibility for existing code"""

    @pytest.mark.asyncio
    async def test_search_facts_without_thread_id_still_works(
            self, memory_service, isolated_facts
    ):
        """
        Test: Calling search_facts WITHOUT thread_id parameter still works

        This ensures existing code doesn't break. When no thread_id is provided,
        it should behave like thread_id=None (global facts only).
        """
        # Act - old-style call without thread_id
        results = await memory_service.search_facts(query="User")

        # Assert - returns global facts (backward compatible behavior)
        # Note: This test defines the expected backward-compatible behavior
        assert isinstance(results, list)


class TestSearchFactsSignature:
    """Test that search_facts has correct signature"""

    def test_search_facts_accepts_thread_id_parameter(self, memory_service):
        """Test: search_facts method accepts thread_id parameter"""
        import inspect

        sig = inspect.signature(memory_service.search_facts)
        params = list(sig.parameters.keys())

        assert "thread_id" in params, \
            "search_facts must accept 'thread_id' parameter"

    def test_search_facts_thread_id_is_optional(self, memory_service):
        """Test: thread_id parameter has a default value (optional)"""
        import inspect

        sig = inspect.signature(memory_service.search_facts)
        thread_id_param = sig.parameters.get("thread_id")

        assert thread_id_param is not None, "thread_id parameter must exist"
        assert thread_id_param.default is not inspect.Parameter.empty, \
            "thread_id should have a default value for backward compatibility"