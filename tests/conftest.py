"""
Pytest configuration and fixtures
"""

from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session for each test
    """
    # Create async engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Yield session
    async with async_session() as session:
        yield session
        await session.rollback()

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {"session_id": "test-session-123", "user_id": "test-user-1", "agent_name": "mistral"}


@pytest.fixture
def sample_fact_data():
    """Sample user fact data for testing"""
    return {
        "fact_id": "fact-123",
        "text": "User prefers Python programming",
        "importance": 0.8,
        "confidence": 0.9,
        "tags": ["programming", "preference"],
        "source": "conversation",
    }
