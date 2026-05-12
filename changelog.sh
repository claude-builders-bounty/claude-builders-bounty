#!/usr/bin/env bash
set -euo pipefail

if command -v python3 >/dev/null 2>&1; then
  python3 generate_changelog.py "$@"
else
  python generate_changelog.py "$@"
fi
