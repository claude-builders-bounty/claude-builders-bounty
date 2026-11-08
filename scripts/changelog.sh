#!/usr/bin/env bash
# Quick wrapper to run generate_changelog.py
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
python3 "$DIR/generate_changelog.py" "$@"
