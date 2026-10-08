#!/bin/bash
# Generate CHANGELOG.md from git history
# Usage: bash changelog.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is available
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "❌ Error: Python is required but not installed."
    exit 1
fi

# Run the Python script
$PYTHON "$SCRIPT_DIR/generate_changelog.py"
