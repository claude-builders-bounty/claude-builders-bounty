#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/generate_changelog.py" --repo "${1:-.}" --output "${2:-CHANGELOG.md}"
