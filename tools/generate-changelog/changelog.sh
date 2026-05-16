#!/usr/bin/env bash
# Generate structured CHANGELOG.md from git history
# Auto-categorizes commits: Added / Fixed / Changed / Removed
# Usage: bash changelog.sh [--output CHANGELOG.md]

set -euo pipefail

OUTPUT="${2:-CHANGELOG.md}"
REPO="${1:-.}"

# Find Python or use system python3
PYTHON=""
for py in python3 python; do
    if command -v "$py" &>/dev/null; then
        PYTHON="$py"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3 not found. Install Python and try again." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$PYTHON" "$SCRIPT_DIR/generate_changelog.py" --repo "$REPO" --output "$OUTPUT" "$@"
