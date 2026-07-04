#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/changelog.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$SCRIPT_DIR/changelog.py" "$@"
else
  echo "error: python3 or python is required" >&2
  exit 1
fi
