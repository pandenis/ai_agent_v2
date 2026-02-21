"""
Integration test: MemoryWriteCommand + MemoryWriteGate preserve the subject
field end-to-end from extraction through to storage (MEM-002-04, step 12 of 13).

Verifies that subject is not silently discarded at any point in the pipeline:
    Fact(subject=X) → MemoryWriteCommand → MemoryWriteGate → FactModel(subject=X)
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.memory_v2 import Fact, FactModel
from app.schemas.memory_commands import MemoryWriteCommand
from app.services.memory_service import MemoryService
from app.services.memory_write_gate import MemoryWriteGate

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
async def write_gate(test_session):
    """MemoryWriteGate wired to a MemoryService backed by the in-memory session."""
    return MemoryWriteGate(MemoryService(test_session))


@pytest.mark.asyncio
async def test_write_gate_preserves_subject(write_gate, test_session):
    """
    Verifies that a Fact with subject='technology' is stored in the database
    with subject='technology' after passing through MemoryWriteCommand and
    MemoryWriteGate.

    Ensures the subject field is not silently discarded in the write path
    (Fact → MemoryWriteCommand → MemoryWriteGate → memory_service.add_facts()
    → FactModel persisted to DB).
    """
    # Arrange
    fact = Fact(
        fact_id="f1",
        text="FastAPI uses asyncio",
        subject="technology",
        thread_id="t1",
        importance=0.75,
    )
    command = MemoryWriteCommand(
        facts=[fact],
        thread_id="t1",
        source="test",
    )

    # Act
    result = await write_gate.execute(command)
    assert result.success, f"Write gate failed unexpectedly: {result.error}"

    row = await test_session.execute(
        select(FactModel).where(FactModel.fact_id == "f1")
    )
    stored = row.scalar_one_or_none()

    # Assert
    assert stored is not None, "Fact was not persisted to the database"
    assert stored.subject == "technology"


@pytest.mark.asyncio
async def test_write_gate_preserves_user_subject(write_gate, test_session):
    """
    Verifies that a Fact with subject='user' is stored in the database
    with subject='user' after passing through MemoryWriteCommand and
    MemoryWriteGate.

    Complements test_write_gate_preserves_subject by confirming correct
    storage for the 'user' subject bucket, which is also the column default.
    """
    # Arrange
    fact = Fact(
        fact_id="f2",
        text="User lives in Berlin",
        subject="user",
        thread_id="t1",
        importance=0.85,
    )
    command = MemoryWriteCommand(
        facts=[fact],
        thread_id="t1",
        source="test",
    )

    # Act
    result = await write_gate.execute(command)
    assert result.success, f"Write gate failed unexpectedly: {result.error}"

    row = await test_session.execute(
        select(FactModel).where(FactModel.fact_id == "f2")
    )
    stored = row.scalar_one_or_none()

    # Assert
    assert stored is not None, "Fact was not persisted to the database"
    assert stored.subject == "user"
