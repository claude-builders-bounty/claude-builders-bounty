#!/usr/bin/env Bash
set -euo pipefail

# Wrapper around generate_changelog.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: must be run inside a git repository" >&2
  exit 1
}

cd "$REPO_ROOT"
python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
