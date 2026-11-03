#!/usr/bin/env bash
# Entrypoint for generating CHANGELOG.md
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/skills/generate-changelog/generate_changelog.py" "$@"
