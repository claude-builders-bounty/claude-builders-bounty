#!/usr/bin/env bash
# generate-changelog: structured CHANGELOG.md section from git history.
# Thin wrapper around changelog.py so the documented entry point is
# simply: bash changelog.sh [--version X] [--tag TAG] [--prepend CHANGELOG.md]
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/changelog.py" "$@"
