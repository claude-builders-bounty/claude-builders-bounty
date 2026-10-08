#!/usr/bin/env bash
# Structured CHANGELOG Generator Shell Wrapper
set -e
VERSION="${1:-Unreleased}"
python3 "$(dirname "$0")/generate_changelog.py" "$VERSION"
