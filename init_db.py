#!/usr/bin/env python
"""Initialize database with all models"""
import asyncio

# Импортируй все модели
from app.models import Session, ConversationMessage, UserFact
from app.core.database import engine, Base

async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print('✅ Database initialized successfully')
    print('📊 Tables created:')
    for table in Base.metadata.tables.keys():
        print(f'   - {table}')

if __name__ == "__main__":
    asyncio.run(init_db())
