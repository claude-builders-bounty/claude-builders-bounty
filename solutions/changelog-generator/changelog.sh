#!/bin/bash
# changelog.sh — Wrapper script for generate_changelog.py
# Usage: bash changelog.sh [--version X.Y.Z] [--repo /path/to/repo]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
