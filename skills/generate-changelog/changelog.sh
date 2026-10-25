#!/usr/bin/env bash
# Standalone CLI wrapper for Git CHANGELOG generator
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

python3 "${SCRIPT_DIR}/generate_changelog.py" "${TARGET_DIR}"
