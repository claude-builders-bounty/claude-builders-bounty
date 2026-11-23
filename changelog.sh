#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/skills/generate-changelog/generate_changelog.py" "$@"
