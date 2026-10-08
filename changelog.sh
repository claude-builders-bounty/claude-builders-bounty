#!/usr/bin/env bash
# Shell wrapper for changelog generator
VERSION="${1:-Unreleased}"
python3 "$(dirname "$0")/generate_changelog.py" "$VERSION" || py "$(dirname "$0")/generate_changelog.py" "$VERSION"
