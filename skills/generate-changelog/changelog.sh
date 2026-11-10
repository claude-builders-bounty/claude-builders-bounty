#!/usr/bin/env bash
# Structured CHANGELOG.md Generator from Git History
# Usage: bash changelog.sh [--since <tag>] [--version <x.y.z>] [--output CHANGELOG.md]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/generate_changelog.py" "$@"
