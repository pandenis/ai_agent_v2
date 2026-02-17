#!/usr/bin/env bash
# Test the backup script
set -e

# Resolve backup.sh location relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Testing backup.sh ==="

# Create a temp test DB
TEST_DIR=$(mktemp -d)
TEST_DB="$TEST_DIR/test.db"
TEST_BACKUP_DIR="$TEST_DIR/backups"

sqlite3 "$TEST_DB" "CREATE TABLE test(id INTEGER); INSERT INTO test VALUES(1);"

# Run backup
"$SCRIPT_DIR/backup.sh" "$TEST_DB" "$TEST_BACKUP_DIR"

# Verify
BACKUP_COUNT=$(find "$TEST_BACKUP_DIR" -name "agent_backup_*.db" | wc -l)
if [ "$BACKUP_COUNT" -eq 1 ]; then
    echo "✅ PASS: Backup file created"
else
    echo "❌ FAIL: Expected 1 backup, found $BACKUP_COUNT"
    exit 1
fi

# Verify backup is valid
ROWS=$(sqlite3 "$TEST_BACKUP_DIR"/agent_backup_*.db "SELECT COUNT(*) FROM test;")
if [ "$ROWS" -eq 1 ]; then
    echo "✅ PASS: Backup data is valid"
else
    echo "❌ FAIL: Backup data invalid"
    exit 1
fi

# Test retention (create old fake backups)
touch -d "10 days ago" "$TEST_BACKUP_DIR/agent_backup_20200101_000000.db"
touch -d "3 days ago" "$TEST_BACKUP_DIR/agent_backup_20200105_000000.db"

"$SCRIPT_DIR/backup.sh" "$TEST_DB" "$TEST_BACKUP_DIR"

OLD_COUNT=$(find "$TEST_BACKUP_DIR" -name "agent_backup_20200101_*.db" | wc -l)
RECENT_COUNT=$(find "$TEST_BACKUP_DIR" -name "agent_backup_20200105_*.db" | wc -l)

if [ "$OLD_COUNT" -eq 0 ]; then
    echo "✅ PASS: Old backup (10 days) deleted"
else
    echo "❌ FAIL: Old backup not deleted"
    exit 1
fi

if [ "$RECENT_COUNT" -eq 1 ]; then
    echo "✅ PASS: Recent backup (3 days) kept"
else
    echo "❌ FAIL: Recent backup incorrectly deleted"
    exit 1
fi

# Cleanup
rm -rf "$TEST_DIR"

echo "=== All backup tests passed ✅ ==="
