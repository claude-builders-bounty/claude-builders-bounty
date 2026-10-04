#!/usr/bin/env bash
# changelog.sh — Root entry point for changelog generator
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/skills/changelog-generator/changelog.sh"

if [ -f "$TARGET_SCRIPT" ]; then
    exec bash "$TARGET_SCRIPT" "$@"
else
    echo "❌ Error: $TARGET_SCRIPT not found." >&2
    exit 1
fi
