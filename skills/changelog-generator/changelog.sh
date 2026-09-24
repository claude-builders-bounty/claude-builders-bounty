#!/usr/bin/env bash
# Standalone CLI / Claude Code command wrapper for changelog generator
set -e
VERSION="${1:-Unreleased}"
OUTFILE="${2:-CHANGELOG.md}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/generate_changelog.py" "$VERSION" "$OUTFILE"
else
    echo "[-] Error: python3 is required to generate changelog" >&2
    exit 1
fi
