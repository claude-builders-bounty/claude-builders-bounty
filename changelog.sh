#!/usr/bin/env bash
set -euo pipefail

# Thin wrapper required by the bounty acceptance criteria.
# Usage: bash changelog.sh [--repo .] [--output CHANGELOG.md] [--version Unreleased] [--since v1.2.3]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/tools/changelog_generator.py" "$@"
