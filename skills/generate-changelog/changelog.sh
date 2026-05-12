#!/usr/bin/env bash
# changelog.sh — Bash wrapper for generate-changelog.py
# Usage: ./changelog.sh [REPO_PATH] [OUTPUT_FILE]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_PATH="${1:-.}"
OUTPUT_FILE="${2:-CHANGELOG.md}"

python3 "${SCRIPT_DIR}/generate-changelog.py" --repo "${REPO_PATH}" --output "${OUTPUT_FILE}"
