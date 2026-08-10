#!/bin/bash
# changelog.sh — wrapper around changelog_gen.py
# Usage: bash changelog.sh [--out CHANGELOG.md] [--from-tag <tag>]
cd "$(dirname "$0")"
exec python3 changelog_gen.py "$@"
