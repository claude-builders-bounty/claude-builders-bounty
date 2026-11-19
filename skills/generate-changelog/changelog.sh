#!/usr/bin/env bash
# changelog.sh - Generate structured CHANGELOG.md from git history
set -euo pipefail

REPO_DIR="${1:-.}"
OUTPUT_FILE="${2:-CHANGELOG.md}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run python engine
if command -v python3 >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/generate_changelog.py" "$REPO_DIR" "$OUTPUT_FILE"
elif command -v python >/dev/null 2>&1; then
    python "$SCRIPT_DIR/generate_changelog.py" "$REPO_DIR" "$OUTPUT_FILE"
else
    echo "Error: Python 3 is required to run changelog.sh" >&2
    exit 1
fi
