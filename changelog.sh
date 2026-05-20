#!/bin/bash
# generate-changelog-wrapper
# Simple bash wrapper for generate_changelog.py
# Usage: ./changelog.sh [--since-tag TAG] [--output FILE]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
