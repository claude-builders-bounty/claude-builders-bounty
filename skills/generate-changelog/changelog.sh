#!/usr/bin/env bash
# Wrapper script for generate_changelog.py
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-Unreleased}"

python3 "${SCRIPT_DIR}/generate_changelog.py" "$VERSION"
