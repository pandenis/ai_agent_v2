#!/usr/bin/env bash
# AI Agent System — Health Monitor
# Usage: ./scripts/health_check.sh [port]
# Default port: 8000 (production); use 8001 for development
#
# Checks:
# 1. FastAPI server responding
# 2. Health endpoint returns healthy status
# 3. Ollama service running and responding
# 4. Database file exists and is not empty
# 5. Disk space above threshold (>1GB free)
# 6. Memory graph tables exist
#
# Exit codes: 0=all healthy, 1=one or more failures
# Output: Suitable for cron + alerting

# NOTE: Do NOT use set -e — individual check failures must not abort the script.
# Failures are tracked manually via FAIL_COUNT.

PORT="${1:-8000}"
BASE_URL="http://localhost:$PORT"
OLLAMA_URL="http://localhost:11434"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL_COUNT=0
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# ── Helper: print pass/fail and increment counter ─────────────────────────────
check() {
    local name="$1"
    local result="$2"   # 0 = pass, non-zero = fail
    if [ "$result" -eq 0 ]; then
        echo "[$TIMESTAMP] OK  $name"
    else
        echo "[$TIMESTAMP] ERR $name"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "[$TIMESTAMP] === AI Agent Health Check (port $PORT) ==="

# ── 1. FastAPI server responding ──────────────────────────────────────────────
result=0
curl -sf "${BASE_URL}/api/v1/health" -o /dev/null -m 5 2>/dev/null || result=1
check "FastAPI server responding (${BASE_URL}/api/v1/health)" "$result"

# ── 2. Health endpoint content ────────────────────────────────────────────────
HEALTH_RESPONSE=""
HEALTH_RESPONSE=$(curl -sf "${BASE_URL}/api/v1/health" -m 5 2>/dev/null) || true
result=1
if echo "$HEALTH_RESPONSE" | grep -qi "healthy\|\"ok\"\|\"true\""; then
    result=0
fi
check "Health endpoint status (got: ${HEALTH_RESPONSE:-UNREACHABLE})" "$result"

# ── 3. Ollama service ─────────────────────────────────────────────────────────
result=0
curl -sf "${OLLAMA_URL}/api/tags" -o /dev/null -m 5 2>/dev/null || result=1
check "Ollama service (${OLLAMA_URL})" "$result"

# ── 4. Database file exists and non-empty ─────────────────────────────────────
DB_PATH="$PROJECT_ROOT/data/agent.db"
if [ ! -f "$DB_PATH" ]; then
    DB_PATH="$PROJECT_ROOT/data/agent_dev.db"
fi
result=1
if [ -f "$DB_PATH" ] && [ -s "$DB_PATH" ]; then
    result=0
fi
check "Database file ($DB_PATH)" "$result"

# ── 5. Disk space > 1 GB free ─────────────────────────────────────────────────
result=1
FREE_KB=0
FREE_KB=$(df "$PROJECT_ROOT" 2>/dev/null | awk 'NR==2 {print $4}') || true
if [ -n "$FREE_KB" ] && [ "$FREE_KB" -gt 1048576 ] 2>/dev/null; then
    result=0
    FREE_LABEL="$((FREE_KB / 1048576))GB free"
else
    FREE_LABEL="${FREE_KB:-?}KB free — LOW"
fi
check "Disk space ($FREE_LABEL)" "$result"

# ── 6. Memory graph tables exist ──────────────────────────────────────────────
result=1
if [ -f "$DB_PATH" ] && command -v sqlite3 &>/dev/null; then
    TABLES=$(sqlite3 "$DB_PATH" ".tables" 2>/dev/null) || true
    if echo "$TABLES" | grep -q "memory_nodes"; then
        result=0
    fi
fi
check "Memory graph tables (memory_nodes)" "$result"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "[$TIMESTAMP] ALL CHECKS PASSED (6/6)"
    exit 0
else
    echo "[$TIMESTAMP] $FAIL_COUNT CHECK(S) FAILED"
    exit 1
fi
