#!/usr/bin/env bash
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [options]

DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/scripts/generate_changelog.py" -o CHANGELOG.md "$@"
