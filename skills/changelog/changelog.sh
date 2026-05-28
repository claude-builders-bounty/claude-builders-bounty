#!/bin/bash
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--output FILE] [--tag TAG]

# Python is the canonical implementation, use it from the skill directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/changelog.py" "$@"
