"""
Tests for search_facts subject filtering (MEM-002-03, step 9 of 13).

Verifies that search_facts() accepts an optional subject parameter and
applies an AND subject = :subject WHERE clause when provided, while
preserving all-subject behaviour when subject=None.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.memory_v2 import FactModel
from app.services.memory_service import MemoryService

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite engine with all tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create an async session bound to the in-memory engine."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def memory_service(test_session):
    """MemoryService wired to the in-memory test session."""
    return MemoryService(test_session)


@pytest.fixture
async def two_subject_facts(test_session):
    """
    Persist two facts in the same thread with different subjects:
      f1 — subject='technology'
      f2 — subject='user'
    """
    facts = [
        FactModel(
            fact_id="f1",
            text="FastAPI is async",
            subject="technology",
            importance=0.8,
            confidence=0.9,
            thread_id="thread-1",
            fact_type="knowledge",
            source="conversation",
        ),
        FactModel(
            fact_id="f2",
            text="User lives in Paris",
            subject="user",
            importance=0.9,
            confidence=0.95,
            thread_id="thread-1",
            fact_type="static",
            source="conversation",
        ),
    ]
    for fact in facts:
        test_session.add(fact)
    await test_session.commit()
    return facts


@pytest.mark.asyncio
async def test_search_facts_filters_by_subject(memory_service, two_subject_facts):
    """
    Verifies that passing subject='technology' to search_facts() returns only
    facts whose subject column equals 'technology', excluding all other subjects.
    """
    # Arrange — both facts are in thread-1; query="" matches all texts

    # Act
    results = await memory_service.search_facts(
        query="", thread_id="thread-1", subject="technology"
    )

    # Assert — only the technology fact is returned
    result_ids = [f.fact_id for f in results]
    assert "f1" in result_ids, "Technology fact must be in results"
    assert "f2" not in result_ids, "User fact must NOT appear when filtering by subject='technology'"


@pytest.mark.asyncio
async def test_search_facts_no_filter_returns_all_subjects(memory_service, two_subject_facts):
    """
    Verifies that passing subject=None (the default) to search_facts() applies
    no subject filter, returning facts of every subject in the thread.
    """
    # Arrange — both facts are in thread-1; subject=None means no subject filter

    # Act
    results = await memory_service.search_facts(
        query="", thread_id="thread-1", subject=None
    )

    # Assert — both facts are returned regardless of subject
    result_ids = [f.fact_id for f in results]
    assert "f1" in result_ids, "Technology fact must appear when subject=None"
    assert "f2" in result_ids, "User fact must appear when subject=None"
