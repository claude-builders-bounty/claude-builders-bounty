#!/usr/bin/env bash
# Root wrapper for changelog generator
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/skills/changelog-generator/changelog.sh" "$@"
