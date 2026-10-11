#!/usr/bin/env bash
set -euo pipefail

# Run from any directory; the Python implementation resolves the repository
# root and never interpolates user input into a shell command.
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
if [[ "$SCRIPT_DIR" == "$SCRIPT_PATH" ]]; then
  SCRIPT_DIR="."
fi
SCRIPT_DIR="$(CDPATH= cd -- "$SCRIPT_DIR" && pwd)"
cd -- "$SCRIPT_DIR"
exec python3 "$SCRIPT_DIR/scripts/changelog.py" "$@"
