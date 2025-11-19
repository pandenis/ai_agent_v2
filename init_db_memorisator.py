#!/usr/bin/env python
"""
Initialize Memorisator database tables
Simple script for MVP - creates tables without Alembic migrations
"""
import asyncio
import sys

# Add project root to path
sys.path.insert(0, ".")

from app.core.database import Base, engine
from app.models.memory_v2 import AuditHistoryModel, ContextMapModel, FactModel


async def init_memorisator_db():
    """Create Memorisator tables"""
    print("🔧 Initializing Memorisator database...")

    async with engine.begin() as conn:
        # Create only Memorisator tables
        print("📦 Creating facts table...")
        await conn.run_sync(FactModel.metadata.create_all)

        print("📦 Creating context_maps table...")
        await conn.run_sync(ContextMapModel.metadata.create_all)

        print("📦 Creating audit_history table...")
        await conn.run_sync(AuditHistoryModel.metadata.create_all)

    print("\n✅ Memorisator database initialized successfully!")

    # Verify tables
    print("\n🔍 Verifying tables...")
    from sqlalchemy import text

    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
        tables = [row[0] for row in result]

        print(f"📊 Found {len(tables)} tables total:")
        for table in tables:
            print(f"   - {table}")

        # Check Memorisator tables
        memorisator_tables = ["facts", "context_maps", "audit_history"]
        for table in memorisator_tables:
            if table in tables:
                print(f"   ✅ {table} created")
            else:
                print(f"   ❌ {table} missing!")

    print("\n🎉 Done!")


if __name__ == "__main__":
    asyncio.run(init_memorisator_db())
