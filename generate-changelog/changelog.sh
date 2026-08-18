#!/usr/bin/env bash
# Generate CHANGELOG.md from commits since the last git tag.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "Run this inside a git repository." >&2
  exit 1
fi
cd "$ROOT"
exec python3 "$(dirname "$0")/changelog.py" "$@"
