#!/usr/bin/env bash
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$(dirname "$0")/generate_changelog.py" "$@"
fi

exec python "$(dirname "$0")/generate_changelog.py" "$@"
