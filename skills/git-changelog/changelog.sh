#!/usr/bin/env bash
# Entrypoint for Git Changelog Generator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-Unreleased}"
OUTPUT_FILE="${2:-CHANGELOG.md}"

python3 "${SCRIPT_DIR}/generate_changelog.py" "${VERSION}" "${OUTPUT_FILE}"
