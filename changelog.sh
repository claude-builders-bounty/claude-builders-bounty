#!/usr/bin/env bash
# Thin wrapper: bash changelog.sh  →  skills/generate-changelog/scripts/changelog.py
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$ROOT/skills/generate-changelog/scripts/changelog.py"
if [[ ! -f "$SCRIPT" ]]; then
  echo "Missing $SCRIPT" >&2
  exit 1
fi
exec python3 "$SCRIPT" "$@"
