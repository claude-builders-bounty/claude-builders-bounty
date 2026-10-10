#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-Unreleased}"
OUTPUT="${2:-CHANGELOG.md}"

python3 "$SCRIPT_DIR/generate_changelog.py" "$VERSION" "$OUTPUT"
