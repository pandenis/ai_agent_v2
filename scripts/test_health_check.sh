#!/usr/bin/env bash
# Test the health_check.sh script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Testing health_check.sh ==="

# Test with a port where nothing is running — script must not crash and must
# exit 1 to signal failures.
# Capture exit code without letting set -e trigger on the non-zero return.
EXIT_CODE=0
"$SCRIPT_DIR/health_check.sh" 19999 || EXIT_CODE=$?

if [ "$EXIT_CODE" -eq 1 ]; then
    echo "✅ PASS: Script correctly reports failures for unreachable server"
else
    echo "❌ FAIL: Expected exit code 1, got $EXIT_CODE"
    exit 1
fi

echo "=== Health check test passed ==="
