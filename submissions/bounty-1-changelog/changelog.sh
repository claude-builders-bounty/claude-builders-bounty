#!/usr/bin/env bash
set -e
PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null)
"$PYTHON" "$(dirname "$0")/generate_changelog.py" "$@"
