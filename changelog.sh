#!/usr/bin/env bash
# Generate CHANGELOG.md via changelog.py
# If no arguments, writes CHANGELOG.md; otherwise passes args to Python script.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ $# -eq 0 ]; then
    python3 "$SCRIPT_DIR/changelog.py" > "$SCRIPT_DIR/CHANGELOG.md"
    echo "CHANGELOG.md generated."
else
    exec python3 "$SCRIPT_DIR/changelog.py" "$@"
fi
