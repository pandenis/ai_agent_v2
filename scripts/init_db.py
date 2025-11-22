"""
Initialize database with all tables from models
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base
from app.models.session import Session
from app.models.memory import ConversationMessage
from app.models.memory_v2 import FactModel

async def init_db():
    # Create async engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///data/agent.db",
        echo=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("\n✅ Database initialized successfully!")
    print("Tables created:")
    print("  - sessions")
    print("  - conversation_messages")
    print("  - facts (with source_session_id!)")
    print("  - (and others)")

if __name__ == "__main__":
    asyncio.run(init_db())
