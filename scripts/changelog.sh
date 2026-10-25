#!/usr/bin/env bash
# Wrapper to generate CHANGELOG.md
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
