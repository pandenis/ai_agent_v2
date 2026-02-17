#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Testing alert_check.sh ==="

# ── Set up temp environment ───────────────────────────────────────────────────
TEST_DIR=$(mktemp -d)
mkdir -p "$TEST_DIR/logs" "$TEST_DIR/backups"

# Create a sparse 150 MB log file (no disk cost)
truncate -s 150M "$TEST_DIR/logs/app.log" 2>/dev/null \
    || dd if=/dev/zero of="$TEST_DIR/logs/app.log" bs=1M count=1 seek=149 2>/dev/null

# Run — expect warnings: large log + no recent backup → exit 1
EXIT_CODE=0
PROJECT_ROOT="$TEST_DIR" LOG_DIR="$TEST_DIR/logs" BACKUP_DIR="$TEST_DIR/backups" \
    "$SCRIPT_DIR/alert_check.sh" || EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 1 ]; then
    echo "✅ PASS: Correctly detected warnings (large log + no recent backup)"
else
    echo "❌ FAIL: Expected exit code 1 (warnings), got $EXIT_CODE"
    rm -rf "$TEST_DIR"
    exit 1
fi

# ── Verify all-clear path: fresh backup + small log ──────────────────────────
# Replace large log with an empty one
rm -f "$TEST_DIR/logs/app.log"
touch "$TEST_DIR/logs/app.log"

# Create a fresh backup file
touch "$TEST_DIR/backups/agent_backup_$(date +%Y%m%d_%H%M%S).db"

EXIT_CODE2=0
PROJECT_ROOT="$TEST_DIR" LOG_DIR="$TEST_DIR/logs" BACKUP_DIR="$TEST_DIR/backups" \
    "$SCRIPT_DIR/alert_check.sh" || EXIT_CODE2=$?

if [ "$EXIT_CODE2" -eq 0 ]; then
    echo "✅ PASS: All-clear path returns exit code 0"
else
    echo "❌ FAIL: Expected exit code 0 (all clear), got $EXIT_CODE2"
    rm -rf "$TEST_DIR"
    exit 1
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -rf "$TEST_DIR"

echo "=== Alert check tests passed ==="
