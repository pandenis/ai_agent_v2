#!/usr/bin/env bash
# AI Agent System — Alert Check
# Usage: ./scripts/alert_check.sh
#
# Supports environment variable overrides for testability:
#   PROJECT_ROOT, LOG_DIR, BACKUP_DIR
#
# Checks:
# 1. Log files not exceeding size threshold (>100MB = warning)
# 2. Disk usage not exceeding threshold (>90% = warning)
# 3. Backup freshness (last backup < 48 hours ago)
# 4. No error spikes in recent logs (>50 errors in last 1000 lines = warning)
#
# Exit codes: 0=all clear, 1=warnings found
# Output: Summary of alerts (suitable for cron email)

# NOTE: Do NOT use set -e — individual checks must not abort the script.

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Paths — allow env var overrides for testing ───────────────────────────────
PROJECT_ROOT="${PROJECT_ROOT:-$(dirname "$_SCRIPT_DIR")}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"

WARN_COUNT=0
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# ── Helpers ───────────────────────────────────────────────────────────────────
warn() {
    echo "[$TIMESTAMP] WARN $*"
    WARN_COUNT=$((WARN_COUNT + 1))
}

ok() {
    echo "[$TIMESTAMP] OK   $*"
}

echo "[$TIMESTAMP] === AI Agent Alert Check ==="
echo "[$TIMESTAMP]     LOG_DIR=$LOG_DIR"
echo "[$TIMESTAMP]     BACKUP_DIR=$BACKUP_DIR"

# ── Check 1: Log files > 100 MB ───────────────────────────────────────────────
if [ -d "$LOG_DIR" ]; then
    LARGE_LOGS=$(find "$LOG_DIR" -name "*.log" -size +100M 2>/dev/null || true)
    if [ -n "$LARGE_LOGS" ]; then
        while IFS= read -r f; do
            SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
            warn "Large log file: $f (${SIZE})"
        done <<< "$LARGE_LOGS"
    else
        ok "Log file sizes within threshold (<100MB)"
    fi
else
    ok "Log directory does not exist yet — skipping size check"
fi

# ── Check 2: Disk usage > 90% ─────────────────────────────────────────────────
USAGE_PCT=0
USAGE_PCT=$(df "$PROJECT_ROOT" 2>/dev/null | awk 'NR==2 {gsub(/%/,""); print $5}') || true
if [ -n "$USAGE_PCT" ] && [ "$USAGE_PCT" -gt 90 ] 2>/dev/null; then
    warn "Disk usage at ${USAGE_PCT}% (threshold: 90%)"
else
    ok "Disk usage at ${USAGE_PCT:-?}% (below 90% threshold)"
fi

# ── Check 3: Backup freshness (last 48 hours) ─────────────────────────────────
LATEST_BACKUP=""
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(find "$BACKUP_DIR" -name "agent_backup_*.db" -mtime -2 2>/dev/null | head -1) || true
fi
if [ -z "$LATEST_BACKUP" ]; then
    warn "No backup found in the last 48 hours (check backup.sh cron)"
else
    ok "Recent backup found: $(basename "$LATEST_BACKUP")"
fi

# ── Check 4: Error spikes in logs ─────────────────────────────────────────────
# Check both prod (app.log) and dev (app_dev.log) log file names
CHECKED_LOG=""
for LOGFILE in "$LOG_DIR/app.log" "$LOG_DIR/app_dev.log"; do
    if [ -f "$LOGFILE" ]; then
        CHECKED_LOG="$LOGFILE"
        break
    fi
done

if [ -n "$CHECKED_LOG" ]; then
    ERROR_COUNT=0
    ERROR_COUNT=$(tail -1000 "$CHECKED_LOG" 2>/dev/null | grep -ci "error\|critical\|traceback" 2>/dev/null) || true
    if [ "$ERROR_COUNT" -gt 50 ]; then
        warn "Error spike in $(basename "$CHECKED_LOG"): $ERROR_COUNT occurrences in last 1000 lines"
    else
        ok "Error rate in $(basename "$CHECKED_LOG"): $ERROR_COUNT in last 1000 lines (below threshold of 50)"
    fi
else
    ok "No app log file found yet — skipping error spike check"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
if [ "$WARN_COUNT" -eq 0 ]; then
    echo "[$TIMESTAMP] ALL CLEAR — no alerts"
    exit 0
else
    echo "[$TIMESTAMP] $WARN_COUNT ALERT(S) FOUND"
    exit 1
fi
