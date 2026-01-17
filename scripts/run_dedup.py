"""Run deduplication on memory facts"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.services.memory_service import MemoryService
from app.services.memory_auditor import MemoryAuditor

DATABASE_URL = "sqlite+aiosqlite:///./data/agent.db"

async def main():
    print("Starting deduplication with LOWER threshold (0.70)...")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        memory_service = MemoryService(db)
        # Lower threshold to catch more similar facts
        auditor = MemoryAuditor(similarity_threshold=0.70)
        
        print("\n=== DRY RUN ===")
        result = await auditor.deduplicate_all(memory_service, dry_run=True)
        print(f"Groups found: {result.groups_found}")
        print(f"Would delete: {result.facts_deleted} facts")
        
        if result.groups_found > 0:
            confirm = input("\nProceed with deletion? (yes/no): ")
            if confirm.lower() == 'yes':
                print("\n=== EXECUTING ===")
                result = await auditor.deduplicate_all(memory_service, dry_run=False)
                print(f"Merged: {result.facts_merged}")
                print(f"Deleted: {result.facts_deleted}")
                if result.errors:
                    print(f"Errors: {result.errors}")
            else:
                print("Cancelled")
        else:
            print("No duplicates to clean!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
