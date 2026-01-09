"""
Task 35: Cache Performance Fix

This file contains the fix to be applied to app/services/orchestrator/orchestrator.py

PROBLEM:
    Currently only direct strategy responses are cached:
    
    if strategy.strategy == "direct":
        self.response_cache.set(query, result, context=user_context)
    
    This means enhanced and deep_reasoning NEVER get cached,
    resulting in 0.96x "speedup" in benchmarks.

SOLUTION:
    1. Cache direct strategy (TTL: 1 hour) - factual, stable
    2. Cache enhanced strategy (TTL: 30 min) - AI-augmented, less stable
    3. Skip caching deep_reasoning - needs fresh web data

LOCATION IN FILE:
    Look for the section after "# Track metrics" that has:
    
    # Cache direct answers for reuse
    if strategy.strategy == "direct":
        self.response_cache.set(query, result, context=user_context)
        logger.debug("Cached direct response")
"""

# ============================================================
# OLD CODE (to be replaced):
# ============================================================
OLD_CODE = '''
            # Cache direct answers for reuse
            if strategy.strategy == "direct":
                self.response_cache.set(query, result, context=user_context)
                logger.debug("Cached direct response")

            return result'''

# ============================================================
# NEW CODE (replacement):
# ============================================================
NEW_CODE = '''
            # Cache responses based on strategy
            # - direct: cache for 1 hour (factual, stable)
            # - enhanced: cache for 30 min (AI-augmented, may change)
            # - deep_reasoning: don't cache (needs fresh web data)
            if strategy.strategy == "direct":
                self.response_cache.set(
                    query, result, 
                    context=user_context, 
                    strategy="direct"
                )
                logger.debug("Cached direct response (TTL: 1 hour)")
            elif strategy.strategy == "enhanced":
                self.response_cache.set(
                    query, result, 
                    context=user_context, 
                    strategy="enhanced"
                )
                logger.debug("Cached enhanced response (TTL: 30 min)")
            # Note: deep_reasoning not cached - needs fresh web search data

            return result'''

# ============================================================
# COMMANDS FOR DENIS TO RUN:
# ============================================================
COMMANDS = """
# On DEV machine (~/PycharmProjects/ai_agent_v2):

# Step 1: Create feature branch
git checkout main
git pull
git checkout -b feature/task35-cache-fix

# Step 2: Copy test file
cp /path/to/test_cache_enhanced_strategy.py tests/unit/services/orchestrator/

# Step 3: Run test (should FAIL - RED)
python -m pytest tests/unit/services/orchestrator/test_cache_enhanced_strategy.py -v

# Step 4: Apply fix using str_replace in your editor
# OLD: (see OLD_CODE above)
# NEW: (see NEW_CODE above)

# Step 5: Run test again (should PASS - GREEN)
python -m pytest tests/unit/services/orchestrator/test_cache_enhanced_strategy.py -v

# Step 6: Run all tests to check regression
python -m pytest tests/ -v

# Step 7: Commit
git add .
git commit -m "feat(orchestrator): Cache enhanced strategy responses for better performance

- Direct strategy: cached for 1 hour (factual, stable)
- Enhanced strategy: NOW cached for 30 min (AI-augmented)  
- Deep reasoning: not cached (needs fresh web data)

Task 35: Fixes cache speedup from 0.96x to >1.5x"

# Step 8: Push
git push origin feature/task35-cache-fix

# Step 9: E2E verification (see benchmark script below)
"""

print("Task 35 Fix ready. Apply OLD_CODE -> NEW_CODE in orchestrator.py")
