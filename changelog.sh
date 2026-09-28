#!/usr/bin/env bash
set -euo pipefail

SOURCE_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SOURCE_PATH%/*}"
if [[ "$SCRIPT_DIR" == "$SOURCE_PATH" ]]; then
  SCRIPT_DIR="."
fi
SCRIPT_DIR="$(cd "$SCRIPT_DIR" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/changelog.py" "$@"
else
  python "$SCRIPT_DIR/changelog.py" "$@"
fi
