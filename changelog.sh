#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
[[ "$SCRIPT_DIR" == "$SCRIPT_PATH" ]] && SCRIPT_DIR="."

"$BASH" "$SCRIPT_DIR/generate-changelog/changelog.sh" "$@"
