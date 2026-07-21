#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history.
# Wraps changelog_gen.py for one-line usage.
#
# Usage:
#   bash changelog.sh                          # Since last tag, stdout
#   bash changelog.sh --version 1.0.0          # With version label
#   bash changelog.sh --output CHANGELOG.md    # Write to file
#   bash changelog.sh --append --output CHANGELOG.md  # Prepend to existing
#   bash changelog.sh --github owner/repo      # Link commits to GitHub

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer python3, fall back to python
PYTHON=""
if command -v python3 &>/dev/null; then
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "Error: python3 is required but not found." >&2
  exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/changelog_gen.py" "$@"
