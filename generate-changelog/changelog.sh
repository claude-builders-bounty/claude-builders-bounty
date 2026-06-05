#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
[[ "$SCRIPT_DIR" == "$SCRIPT_PATH" ]] && SCRIPT_DIR="."
SCRIPT_DIR="$(cd "$SCRIPT_DIR" && pwd)"

if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
  python "$SCRIPT_DIR/generate_changelog.py" "$@"
else
  py -3 "$SCRIPT_DIR/generate_changelog.py" "$@"
fi
