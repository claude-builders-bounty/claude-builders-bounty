#!/usr/bin/env bash
# Wrapper to generate structured CHANGELOG from git history
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if command -v python3 &>/dev/null; then
    python3 "$DIR/generate_changelog.py"
elif command -v python &>/dev/null; then
    python "$DIR/generate_changelog.py"
else
    echo "Error: Python 3 is required to run generate_changelog.py" >&2
    exit 1
fi
