#!/usr/bin/env python
"""
Migration: Add thread_id column to facts table

Epic 1: Thread Isolation
Task 1.1: Add thread_id column

This migration adds thread_id for fact isolation per session/thread.
Existing facts will have thread_id = NULL (backward compatible).
"""
import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import text
from app.core.database import engine


async def migrate():
    """Add thread_id column to facts table"""
    print("🔧 Migration: Add thread_id to facts table")
    print("=" * 50)

    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("PRAGMA table_info(facts)"))
        columns = [row[1] for row in result.fetchall()]

        if "thread_id" in columns:
            print("✅ Column 'thread_id' already exists. Skipping.")
            return

        # Add thread_id column
        print("📦 Adding 'thread_id' column...")
        await conn.execute(text("""
                                ALTER TABLE facts
                                    ADD COLUMN thread_id VARCHAR(64)
                                """))

        # Create index for performance
        print("📦 Creating index on 'thread_id'...")
        await conn.execute(text("""
                                CREATE INDEX IF NOT EXISTS ix_facts_thread_id
                                    ON facts(thread_id)
                                """))

        print("✅ Migration complete!")

    # Verify
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(facts)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"\n📊 Facts table columns: {columns}")

        if "thread_id" in columns:
            print("✅ Verified: thread_id column exists")
        else:
            print("❌ ERROR: thread_id column not found!")


async def rollback():
    """Remove thread_id column (SQLite limitation: requires table rebuild)"""
    print("⚠️  SQLite doesn't support DROP COLUMN directly.")
    print("    For rollback, restore from backup or recreate table.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())