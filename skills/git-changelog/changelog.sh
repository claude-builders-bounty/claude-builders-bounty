#!/usr/bin/env bash
# changelog.sh - Generate structured CHANGELOG.md from git history

set -e

python3 "$(dirname "$0")/generate_changelog.py" || python "$(dirname "$0")/generate_changelog.py"