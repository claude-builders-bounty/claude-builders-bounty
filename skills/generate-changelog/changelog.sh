#!/usr/bin/env bash
# Thin wrapper: bash changelog.sh [args...]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/changelog_from_git.py" "$@"
