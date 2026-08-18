#!/usr/bin/env bash
# Git Changelog Generator for Claude Code & CI/CD
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-Unreleased}"
OUTPUT="${2:-CHANGELOG.md}"

python3 "${SCRIPT_DIR}/generate_changelog.py" --version "${VERSION}" --output "${OUTPUT}" --prepend
