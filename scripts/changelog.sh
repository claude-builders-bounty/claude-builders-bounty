#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
VERSION="${1:-Unreleased}"

python3 "$DIR/generate_changelog.py" "$VERSION"
