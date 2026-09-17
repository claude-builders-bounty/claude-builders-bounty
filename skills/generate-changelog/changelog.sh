#!/usr/bin/env bash
# Wrapper to generate structured CHANGELOG from git history
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-Unreleased}"

python3 "$SCRIPT_DIR/changelog.py" "$VERSION"
