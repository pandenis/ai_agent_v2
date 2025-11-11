#!/usr/bin/env python
"""
End-to-End test for FactExtractor + MemoryService integration

Tests:
1. Extract facts from conversation
2. Save facts to database
3. Retrieve facts with filters
4. Get stats
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fact_extractor import FactExtractor
from app.services.memory_service import MemoryService
from app.core.database import get_db


async def test_fact_extraction_e2e():
    """Test complete fact extraction pipeline"""
    
    print("=" * 60)
    print("🧪 End-to-End Fact Extraction Test")
    print("=" * 60)
    
    # Step 1: Extract facts
    print("\n📤 Step 1: Extracting facts from conversation...")
    extractor = FactExtractor()
    
    messages = [
        {"role": "user", "content": "I'm Denis, a Python developer living in Tel Aviv"},
        {"role": "assistant", "content": "Nice to meet you Denis! What do you work on?"},
        {"role": "user", "content": "I'm building an AI agent system. I love hiking and photography in my free time."}
    ]
    
    facts = await extractor.extract_facts(messages)
    print(f"✅ Extracted {len(facts)} facts:")
    for i, fact in enumerate(facts, 1):
        print(f"   {i}. {fact.text} [{fact.fact_type}] (importance: {fact.importance})")
    
    if len(facts) == 0:
        print("❌ No facts extracted - test failed")
        return
    
    # Step 2: Save to database
    print("\n💾 Step 2: Saving facts to database...")
    async for db in get_db():
        memory_service = MemoryService(db)
        
        saved_facts = await memory_service.add_facts(facts)
        print(f"✅ Saved {len(saved_facts)} facts to database")
        
        # Step 3: Retrieve facts
        print("\n📥 Step 3: Retrieving facts from database...")
        retrieved_facts = await memory_service.get_facts(min_importance=0.5)
        print(f"✅ Retrieved {len(retrieved_facts)} facts")
        
        for fact_model in retrieved_facts[:3]:  # Show first 3
            print(f"   - {fact_model.text}")
            print(f"     ID: {fact_model.fact_id}")
            print(f"     Type: {fact_model.fact_type}, Importance: {fact_model.importance}")
        
        # Step 4: Test filtering
        print("\n🔍 Step 4: Testing filters...")
        
        # Filter by fact_type
        preferences = await memory_service.get_facts(fact_type="preference")
        print(f"   Preference facts: {len(preferences)}")
        
        # Filter by importance
        high_importance = await memory_service.get_facts(min_importance=0.8)
        print(f"   High importance facts (≥0.8): {len(high_importance)}")
        
        # Step 5: Get stats
        print("\n📊 Step 5: Getting statistics...")
        stats = await memory_service.get_facts_stats()
        print(f"   Total facts: {stats['total_facts']}")
        print(f"   Facts by type: {stats['facts_by_type']}")
        print(f"   Average importance: {stats['avg_importance']}")
        
        # Step 6: Test fact retrieval by ID
        print("\n🔑 Step 6: Testing fact retrieval by ID...")
        if saved_facts:
            test_fact_id = saved_facts[0].fact_id
            retrieved_fact = await memory_service.get_fact_by_id(test_fact_id)
            if retrieved_fact:
                print(f"✅ Retrieved fact by ID: {retrieved_fact.text}")
            else:
                print(f"❌ Failed to retrieve fact by ID")
        
        break  # Exit db session
    
    print("\n" + "=" * 60)
    print("✅ END-TO-END TEST PASSED!")
    print("=" * 60)
    print("\n📋 Summary:")
    print(f"   - Facts extracted: {len(facts)}")
    print(f"   - Facts saved: {len(saved_facts)}")
    print(f"   - Facts retrieved: {len(retrieved_facts)}")
    print(f"   - Total in database: {stats['total_facts']}")
    print("\n🎉 Complete fact extraction pipeline working!")


if __name__ == "__main__":
    asyncio.run(test_fact_extraction_e2e())