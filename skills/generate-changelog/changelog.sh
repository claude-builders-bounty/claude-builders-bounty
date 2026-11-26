#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Thin wrapper around the single source of truth,
# generate_changelog.py (pure Python stdlib, no dependencies).
# All classification logic lives in the Python engine; this script
# exists only so the bounty acceptance criterion
# "works via `bash changelog.sh`" is met literally.
#
# Usage:
#   bash changelog.sh [--output CHANGELOG.md] [--since <ref>] [--unreleased]
#                     [--version X.Y.Z] [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "error: python3 is required (generate_changelog.py is pure stdlib)." >&2
  exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/generate_changelog.py" "$@"
