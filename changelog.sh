#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/generate_changelog.py" "$@"
else
  echo "Python 3 is required to generate the changelog." >&2
  exit 1
fi
