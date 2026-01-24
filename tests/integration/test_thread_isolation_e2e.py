"""
End-to-End Integration Tests for Thread Isolation

Epic 1: Thread Isolation - FINAL VERIFICATION
Task 1.5: Integration tests proving all Epic 1 features work together

These tests verify:
1. Complete thread isolation (no cross-thread leakage)
2. Full lifecycle (create → search → update → delete)
3. Concurrent threads with many facts
4. Session reset clears only target thread
5. Global vs thread-specific fact handling

This is the FINAL validation that Epic 1 is production-ready.
"""
import pytest
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


class TestThreadIsolationE2E:
    """
    End-to-End tests for complete thread isolation.

    These tests simulate real user scenarios with multiple
    independent conversation threads.
    """

    @pytest.mark.asyncio
    async def test_complete_thread_lifecycle(self, memory_service):
        """
        Test: Complete lifecycle of a thread from creation to deletion.
        """
        thread_id = "lifecycle-test-thread"

        # Step 1: Create initial facts
        initial_facts = [
            Fact(fact_id="life-1", text="User likes coffee", thread_id=thread_id, importance=0.8),
            Fact(fact_id="life-2", text="User works remotely", thread_id=thread_id, importance=0.9),
        ]
        saved = await memory_service.add_facts(initial_facts)
        assert len(saved) == 2

        # Step 2: Search facts (should find both)
        results = await memory_service.search_facts(query="User", thread_id=thread_id, limit=100)
        assert len(results) == 2

        # Step 3: Add more facts
        more_facts = [
            Fact(fact_id="life-3", text="User prefers morning meetings", thread_id=thread_id, importance=0.7),
        ]
        await memory_service.add_facts(more_facts)

        # Step 4: Search again (finds all 3)
        results = await memory_service.search_facts(query="User", thread_id=thread_id, limit=100)
        assert len(results) == 3

        # Step 5: Clear thread
        deleted = await memory_service.clear_thread_facts(thread_id)
        assert deleted == 3

        # Step 6: Verify empty
        results = await memory_service.search_facts(query="User", thread_id=thread_id, limit=100)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_multiple_concurrent_threads(self, memory_service):
        """
        Test: Multiple threads operating concurrently with strict isolation.
        """
        # Create facts in different threads
        await memory_service.add_facts([
            Fact(fact_id="dev-1", text="Python developer skills", thread_id="thread-dev", importance=0.8),
            Fact(fact_id="dev-2", text="Likes TDD methodology", thread_id="thread-dev", importance=0.8),
        ])
        await memory_service.add_facts([
            Fact(fact_id="chef-1", text="Chef specializes cooking", thread_id="thread-chef", importance=0.8),
            Fact(fact_id="chef-2", text="Italian cuisine expert", thread_id="thread-chef", importance=0.8),
        ])

        # Cross-thread isolation check
        chef_python = await memory_service.search_facts(query="Python", thread_id="thread-chef", limit=100)
        assert len(chef_python) == 0, "Chef's thread should NOT see Python facts!"

        dev_chef = await memory_service.search_facts(query="Chef", thread_id="thread-dev", limit=100)
        assert len(dev_chef) == 0, "Developer's thread should NOT see Chef facts!"

        # Each thread sees its own
        dev_facts = await memory_service.search_facts(query="Python", thread_id="thread-dev", limit=100)
        assert len(dev_facts) == 1

        chef_facts = await memory_service.search_facts(query="Chef", thread_id="thread-chef", limit=100)
        assert len(chef_facts) == 1

    @pytest.mark.asyncio
    async def test_thread_isolation_after_session_reset(self, memory_service):
        """
        Test: Clearing one thread does NOT affect other threads.
        """
        # Create 3 threads
        await memory_service.add_facts([
            Fact(fact_id="keep1-1", text="Keep this fact 1", thread_id="thread-keep-1"),
            Fact(fact_id="keep1-2", text="Keep this fact 2", thread_id="thread-keep-1"),
        ])
        await memory_service.add_facts([
            Fact(fact_id="del-1", text="Delete this fact 1", thread_id="thread-delete"),
            Fact(fact_id="del-2", text="Delete this fact 2", thread_id="thread-delete"),
            Fact(fact_id="del-3", text="Delete this fact 3", thread_id="thread-delete"),
        ])
        await memory_service.add_facts([
            Fact(fact_id="keep2-1", text="Another keep fact", thread_id="thread-keep-2"),
        ])

        # Clear only the middle thread
        deleted_count = await memory_service.clear_thread_facts("thread-delete")
        assert deleted_count == 3

        # Other threads untouched
        keep1_after = await memory_service.search_facts(query="Keep", thread_id="thread-keep-1", limit=100)
        delete_after = await memory_service.search_facts(query="Delete", thread_id="thread-delete", limit=100)
        keep2_after = await memory_service.search_facts(query="keep", thread_id="thread-keep-2", limit=100)

        assert len(keep1_after) == 2, "thread-keep-1 must be untouched!"
        assert len(delete_after) == 0, "thread-delete must be empty!"
        assert len(keep2_after) == 1, "thread-keep-2 must be untouched!"

    @pytest.mark.asyncio
    async def test_global_vs_thread_specific_facts(self, memory_service):
        """
        Test: Global facts (thread_id=None) are separate from thread-specific facts.
        """
        # Create global and thread-specific facts
        await memory_service.add_facts([
            Fact(fact_id="global-1", text="User name is Denis", thread_id=None, importance=0.95),
        ])
        await memory_service.add_facts([
            Fact(fact_id="thread-1", text="Discussing Python project", thread_id="work-thread", importance=0.8),
        ])

        # Thread should NOT see global
        thread_results = await memory_service.search_facts(query="Denis", thread_id="work-thread", limit=100)
        assert len(thread_results) == 0, "Thread search should NOT see global facts!"

        # Global should NOT see thread
        global_results = await memory_service.search_facts(query="Python", thread_id=None, limit=100)
        assert len(global_results) == 0, "Global search should NOT see thread facts!"

        # Each sees its own
        global_own = await memory_service.search_facts(query="Denis", thread_id=None, limit=100)
        thread_own = await memory_service.search_facts(query="Python", thread_id="work-thread", limit=100)
        assert len(global_own) == 1
        assert len(thread_own) == 1


class TestThreadIsolationStress:
    """Stress tests for thread isolation with larger data volumes."""

    @pytest.mark.asyncio
    async def test_many_facts_per_thread(self, memory_service):
        """Test: Thread with many facts maintains isolation."""
        thread_a = "thread-many-a"
        thread_b = "thread-many-b"
        num_facts_a = 50
        num_facts_b = 30

        # Create facts in thread A
        facts_a = [
            Fact(
                fact_id=f"many-a-{i}",
                text=f"AlphaContent item{i}",
                thread_id=thread_a,
                importance=0.7
            )
            for i in range(num_facts_a)
        ]
        saved_a = await memory_service.add_facts(facts_a)
        assert len(saved_a) == num_facts_a, f"Should save {num_facts_a} facts to A"

        # Create facts in thread B
        facts_b = [
            Fact(
                fact_id=f"many-b-{i}",
                text=f"BetaContent item{i}",
                thread_id=thread_b,
                importance=0.7
            )
            for i in range(num_facts_b)
        ]
        saved_b = await memory_service.add_facts(facts_b)
        assert len(saved_b) == num_facts_b, f"Should save {num_facts_b} facts to B"

        # Search A - should find all A facts
        results_a = await memory_service.search_facts(
            query="AlphaContent",
            thread_id=thread_a,
            limit=200,
            min_importance=0.0
        )
        assert len(results_a) == num_facts_a, f"Thread A should find {num_facts_a} facts, got {len(results_a)}"

        # Search B - should find all B facts
        results_b = await memory_service.search_facts(
            query="BetaContent",
            thread_id=thread_b,
            limit=200,
            min_importance=0.0
        )
        assert len(results_b) == num_facts_b, f"Thread B should find {num_facts_b} facts, got {len(results_b)}"

        # Cross-check: A should NOT see B
        cross_check = await memory_service.search_facts(query="BetaContent", thread_id=thread_a, limit=200)
        assert len(cross_check) == 0, "Thread A must NOT see Thread B facts!"

    @pytest.mark.asyncio
    async def test_many_threads(self, memory_service):
        """Test: Multiple threads each with facts maintains isolation."""
        num_threads = 10
        facts_per_thread = 5

        # Create all threads
        for t in range(num_threads):
            thread_id = f"stress-thread-{t}"
            facts = [
                Fact(
                    fact_id=f"stress-{t}-{i}",
                    text=f"UniqueWord{t} item{i}",
                    thread_id=thread_id,
                    importance=0.7
                )
                for i in range(facts_per_thread)
            ]
            saved = await memory_service.add_facts(facts)
            assert len(saved) == facts_per_thread, f"Thread {t} should save {facts_per_thread}"

        # Verify first thread can find its facts
        results_0 = await memory_service.search_facts(
            query="UniqueWord0",
            thread_id="stress-thread-0",
            limit=50,
            min_importance=0.0
        )
        assert len(results_0) == facts_per_thread, f"Thread 0 should find {facts_per_thread}"

        # Cross-thread check
        cross = await memory_service.search_facts(query="UniqueWord9", thread_id="stress-thread-0", limit=50)
        assert len(cross) == 0, "Thread 0 must NOT see Thread 9 facts!"

    @pytest.mark.asyncio
    async def test_clear_one_thread_preserves_others_at_scale(self, memory_service):
        """Test: Clearing one thread among many preserves all others."""
        num_threads = 5
        facts_per_thread = 10
        thread_to_clear = 2

        # Create all threads
        for t in range(num_threads):
            thread_id = f"scale-thread-{t}"
            facts = [
                Fact(
                    fact_id=f"scale-{t}-{i}",
                    text=f"ScaleWord{t} number{i}",
                    thread_id=thread_id,
                    importance=0.7
                )
                for i in range(facts_per_thread)
            ]
            await memory_service.add_facts(facts)

        # Clear thread 2
        deleted = await memory_service.clear_thread_facts(f"scale-thread-{thread_to_clear}")
        assert deleted == facts_per_thread

        # Verify OTHER threads still have their facts
        for t in range(num_threads):
            thread_id = f"scale-thread-{t}"
            results = await memory_service.search_facts(
                query=f"ScaleWord{t}",
                thread_id=thread_id,
                limit=50,
                min_importance=0.0
            )

            if t == thread_to_clear:
                assert len(results) == 0, f"Cleared thread {t} should be empty!"
            else:
                assert len(results) == facts_per_thread, \
                    f"Thread {t} should have {facts_per_thread} facts, got {len(results)}"


class TestEpic1CompletionVerification:
    """
    Final verification that all Epic 1 requirements are met.
    """

    @pytest.mark.asyncio
    async def test_epic1_requirement_thread_isolation(self, memory_service):
        """
        REQUIREMENT: Facts in Thread A never appear in Thread B queries.
        """
        await memory_service.add_facts([
            Fact(fact_id="req1-a", text="SecretA data", thread_id="thread-A", importance=0.8),
            Fact(fact_id="req1-b", text="SecretB data", thread_id="thread-B", importance=0.8),
        ])

        # A cannot see B
        a_sees_b = await memory_service.search_facts(query="SecretB", thread_id="thread-A", limit=100)
        assert len(a_sees_b) == 0, "FAILED: Thread A can see Thread B data!"

        # B cannot see A
        b_sees_a = await memory_service.search_facts(query="SecretA", thread_id="thread-B", limit=100)
        assert len(b_sees_a) == 0, "FAILED: Thread B can see Thread A data!"

        # Each sees only its own
        a_own = await memory_service.search_facts(query="SecretA", thread_id="thread-A", limit=100)
        b_own = await memory_service.search_facts(query="SecretB", thread_id="thread-B", limit=100)

        assert len(a_own) == 1
        assert len(b_own) == 1

    @pytest.mark.asyncio
    async def test_epic1_requirement_session_reset(self, memory_service):
        """
        REQUIREMENT: Session reset clears thread-specific working memory.
        """
        thread_id = "session-to-reset"

        await memory_service.add_facts([
            Fact(fact_id=f"reset-{i}", text=f"ResetFact{i}", thread_id=thread_id, importance=0.7)
            for i in range(10)
        ])

        # Verify facts exist
        before = await memory_service.search_facts(query="ResetFact", thread_id=thread_id, limit=20)
        assert len(before) == 10

        # Reset session
        cleared = await memory_service.clear_thread_facts(thread_id)
        assert cleared == 10

        # Verify empty
        after = await memory_service.search_facts(query="ResetFact", thread_id=thread_id, limit=20)
        assert len(after) == 0, "FAILED: Session reset did not clear all facts!"

    @pytest.mark.asyncio
    async def test_epic1_all_features_combined(self, memory_service):
        """
        FINAL TEST: All Epic 1 features working together.
        """
        work_thread = "work-conversation"
        personal_thread = "personal-conversation"

        # Start both conversations
        await memory_service.add_facts([
            Fact(fact_id="w1", text="WorkDeadline Monday", thread_id=work_thread, importance=0.9),
            Fact(fact_id="w2", text="WorkMeeting 2pm", thread_id=work_thread, importance=0.8),
            Fact(fact_id="w3", text="WorkClient blue", thread_id=work_thread, importance=0.85),
        ])
        await memory_service.add_facts([
            Fact(fact_id="p1", text="PersonalDoctor Thursday", thread_id=personal_thread, importance=0.95),
            Fact(fact_id="p2", text="PersonalGift mom", thread_id=personal_thread, importance=0.7),
        ])

        # Verify isolation
        work_sees_personal = await memory_service.search_facts(query="PersonalDoctor", thread_id=work_thread, limit=100)
        personal_sees_work = await memory_service.search_facts(query="WorkDeadline", thread_id=personal_thread, limit=100)

        assert len(work_sees_personal) == 0, "Work thread sees personal data!"
        assert len(personal_sees_work) == 0, "Personal thread sees work data!"

        # Reset work thread
        cleared = await memory_service.clear_thread_facts(work_thread)
        assert cleared == 3

        # Personal thread intact
        personal_after = await memory_service.search_facts(query="PersonalDoctor", thread_id=personal_thread, limit=100)
        assert len(personal_after) == 1, "Personal thread was affected by work reset!"

        # Fresh start in work thread
        await memory_service.add_facts([
            Fact(fact_id="w-new", text="NewWorkProject started", thread_id=work_thread, importance=0.9)
        ])

        fresh_results = await memory_service.search_facts(query="NewWorkProject", thread_id=work_thread, limit=100)
        assert len(fresh_results) == 1

        # Old work facts still gone
        old_work = await memory_service.search_facts(query="WorkDeadline", thread_id=work_thread, limit=100)
        assert len(old_work) == 0, "Old work facts reappeared!"