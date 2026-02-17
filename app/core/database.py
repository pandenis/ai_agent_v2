"""
Database setup with SQLAlchemy async support
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)  # Log SQL queries in debug mode

# Create async session factory
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine/session for components that require synchronous DB access
# (e.g., MemoryMapRepository). Derived from the same DB URL.
_sync_url = settings.database_url.replace("+aiosqlite", "")
sync_engine = create_engine(_sync_url, echo=False)
SyncSessionFactory = sessionmaker(bind=sync_engine, class_=Session)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
