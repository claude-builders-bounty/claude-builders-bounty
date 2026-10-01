#!/usr/bin/env bash
# Standalone bash wrapper for /generate-changelog
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/generate_changelog.py"
