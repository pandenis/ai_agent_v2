#!/bin/bash
# Task 35: E2E Cache Verification Script
# Run this on production server after deploying the fix

echo "=============================================="
echo "Task 35: Cache Performance E2E Verification"
echo "=============================================="
echo ""

API_URL="${API_URL:-http://localhost:8000}"
SESSION_ID="cache-test-$(date +%s)"

echo "API URL: $API_URL"
echo "Session: $SESSION_ID"
echo ""

# Test 1: Simple query (should trigger enhanced strategy)
echo "=== Test 1: First Request (should be ~3-9s) ==="
echo "Query: What programming language is best for beginners?"
echo ""

START1=$(date +%s.%N)
RESPONSE1=$(curl -s -X POST "$API_URL/api/v1/orchestrate" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What programming language is best for beginners?\",
    \"session_id\": \"$SESSION_ID\"
  }")
END1=$(date +%s.%N)
TIME1=$(echo "$END1 - $START1" | bc)

echo "Response time: ${TIME1}s"
STRATEGY1=$(echo $RESPONSE1 | python3 -c "import sys,json; print(json.load(sys.stdin).get('metadata',{}).get('strategy','unknown'))" 2>/dev/null)
echo "Strategy: $STRATEGY1"
echo ""

# Test 2: Same query (should be from cache if fix works)
echo "=== Test 2: Second Request (should be <0.5s if cached) ==="
echo "Query: What programming language is best for beginners? (same)"
echo ""

START2=$(date +%s.%N)
RESPONSE2=$(curl -s -X POST "$API_URL/api/v1/orchestrate" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What programming language is best for beginners?\",
    \"session_id\": \"$SESSION_ID\"
  }")
END2=$(date +%s.%N)
TIME2=$(echo "$END2 - $START2" | bc)

echo "Response time: ${TIME2}s"
CACHED=$(echo $RESPONSE2 | python3 -c "import sys,json; print(json.load(sys.stdin).get('metadata',{}).get('cached',False))" 2>/dev/null)
echo "Cached: $CACHED"
echo ""

# Calculate speedup
SPEEDUP=$(echo "scale=2; $TIME1 / $TIME2" | bc)
echo "=============================================="
echo "RESULTS"
echo "=============================================="
echo "First request:  ${TIME1}s"
echo "Second request: ${TIME2}s"
echo "Speedup:        ${SPEEDUP}x"
echo "Cached flag:    $CACHED"
echo ""

# Check if fix worked
if (( $(echo "$SPEEDUP > 1.5" | bc -l) )) && [ "$CACHED" == "True" ]; then
    echo "✅ SUCCESS: Cache fix is working!"
    echo "   Speedup > 1.5x and cached=True"
    exit 0
elif (( $(echo "$SPEEDUP > 1.5" | bc -l) )); then
    echo "⚠️ PARTIAL: Good speedup but cached flag not set"
    exit 0
else
    echo "❌ FAIL: Cache speedup is only ${SPEEDUP}x (target >1.5x)"
    echo "   This indicates the cache fix may not be applied."
    exit 1
fi
