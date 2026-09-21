#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO="${1:-$PWD}"
exec python3 "$ROOT/scripts/generate_changelog.py" --repo "$REPO" --output CHANGELOG.md
