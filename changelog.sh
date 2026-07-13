#!/usr/bin/env bash
# changelog.sh — thin wrapper around changelog.py
# Usage: bash changelog.sh [output-file]
exec python3 "$(dirname "$0")/changelog.py" "$@"
