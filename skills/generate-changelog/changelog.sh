#!/usr/bin/env bash
# ==============================================================================
# changelog.sh — Wrapper to generate CHANGELOG.md from git history
# ==============================================================================
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/changelog.py" "$@"
