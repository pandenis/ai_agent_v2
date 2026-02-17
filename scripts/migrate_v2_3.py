#!/usr/bin/env python
"""
Migration: Create memory_nodes and memory_edges tables

Epic 8: Graph-based Memory Persistence
Step 5: Add tables for MemoryMap graph storage

Idempotent — safe to run multiple times.
Uses synchronous SQLAlchemy (no asyncio needed).

Usage:
    python scripts/migrate_v2_3.py
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect
from app.core.config import settings
from app.core.database import Base
from app.models.memory_graph import MemoryEdgeModel, MemoryNodeModel


def migrate():
    """Create memory_nodes and memory_edges tables if they don't exist."""
    # Derive sync URL from app config (strip async driver)
    db_url = settings.database_url.replace("+aiosqlite", "")
    engine = create_engine(db_url)

    print("Migration: Create memory graph tables (v2.3)")
    print("=" * 50)
    print(f"  Database: {db_url}")

    inspector = inspect(engine)
    existing = inspector.get_table_names()
    print(f"  Existing tables: {existing}")

    target_tables = [MemoryNodeModel.__table__, MemoryEdgeModel.__table__]

    for table in target_tables:
        if table.name in existing:
            print(f"  Table '{table.name}' already exists. Skipping.")
        else:
            print(f"  Creating table '{table.name}'...")

    # create_all is idempotent (checkfirst=True by default)
    Base.metadata.create_all(engine, tables=target_tables)

    # Verify
    inspector = inspect(engine)
    existing = inspector.get_table_names()
    for table in target_tables:
        if table.name in existing:
            print(f"  Verified: '{table.name}' exists")
        else:
            print(f"  ERROR: '{table.name}' not found!")

    engine.dispose()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
