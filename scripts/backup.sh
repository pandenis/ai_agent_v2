#!/usr/bin/env bash
# AI Agent System — Automated Database Backup
# Usage: ./scripts/backup.sh [db_path] [backup_dir]
# Defaults: db_path=data/agent.db, backup_dir=backups/
#
# Features:
# - Copies SQLite DB using sqlite3 .backup (safe, handles WAL)
# - Timestamped filenames: agent_backup_YYYYMMDD_HHMMSS.db
# - 7-day retention: deletes backups older than 7 days
# - Exit codes: 0=success, 1=error
# - Logs to stdout (suitable for cron)

set -e

# ── Resolve script's project root (works from any working dir) ────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Configurable defaults ─────────────────────────────────────────────────────
DEFAULT_DB_PATH="data/agent.db"
DEFAULT_BACKUP_DIR="backups"

# ── Arguments (override defaults) ────────────────────────────────────────────
DB_PATH="${1:-$DEFAULT_DB_PATH}"
BACKUP_DIR="${2:-$DEFAULT_BACKUP_DIR}"

# ── Resolve to absolute paths relative to project root ───────────────────────
if [[ "$DB_PATH" != /* ]]; then
    DB_PATH="$PROJECT_ROOT/$DB_PATH"
fi
if [[ "$BACKUP_DIR" != /* ]]; then
    BACKUP_DIR="$PROJECT_ROOT/$BACKUP_DIR"
fi

# ── Timestamp for this run ────────────────────────────────────────────────────
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/agent_backup_${TIMESTAMP}.db"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ── Validate source DB ────────────────────────────────────────────────────────
if [[ ! -f "$DB_PATH" ]]; then
    log "ERROR: Database not found: $DB_PATH"
    exit 1
fi

log "Starting backup: $DB_PATH -> $BACKUP_FILE"

# ── Create backup directory ───────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"

# ── Perform backup ────────────────────────────────────────────────────────────
if command -v sqlite3 &>/dev/null; then
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
    log "Backup method: sqlite3 .backup (WAL-safe)"
else
    log "WARNING: sqlite3 not found, falling back to cp"
    cp "$DB_PATH" "$BACKUP_FILE"
    log "Backup method: cp"
fi

# ── Verify backup ─────────────────────────────────────────────────────────────
if [[ ! -f "$BACKUP_FILE" ]]; then
    log "ERROR: Backup file was not created: $BACKUP_FILE"
    exit 1
fi

BACKUP_SIZE=$(wc -c < "$BACKUP_FILE")
if [[ "$BACKUP_SIZE" -eq 0 ]]; then
    log "ERROR: Backup file is empty: $BACKUP_FILE"
    rm -f "$BACKUP_FILE"
    exit 1
fi

log "Backup verified: $BACKUP_FILE (${BACKUP_SIZE} bytes)"

# ── 7-day retention ───────────────────────────────────────────────────────────
DELETED=$(find "$BACKUP_DIR" -name "agent_backup_*.db" -mtime +7 -print)
if [[ -n "$DELETED" ]]; then
    echo "$DELETED" | while IFS= read -r old_file; do
        log "Deleting old backup: $old_file"
    done
    find "$BACKUP_DIR" -name "agent_backup_*.db" -mtime +7 -delete
else
    log "Retention: no backups older than 7 days to remove"
fi

log "Backup complete."
