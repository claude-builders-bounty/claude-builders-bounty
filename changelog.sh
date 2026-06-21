#!/usr/bin/env bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [repo_path] [since_tag] [output_file]
#
# Requires: Python 3.x

REPO_PATH="${1:-.}"
SINCE_TAG="${2:-}"
OUTPUT_FILE="${3:-CHANGELOG.md}"

# Resolve absolute paths
REPO_PATH="$(cd "$REPO_PATH" 2>/dev/null && pwd)"
OUTPUT_FILE="$(cd "$(dirname "$OUTPUT_FILE")" 2>/dev/null && pwd)/$(basename "$OUTPUT_FILE")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/generate_changelog.py" "$REPO_PATH" "$SINCE_TAG" "$OUTPUT_FILE"
