#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the last tag.
# Usage: bash bounty1/changelog.sh [repo_path]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${1:-$ROOT}"
exec python3 "$ROOT/bounty1/generate_changelog.py" --repo "$REPO" --output "$REPO/CHANGELOG.md"
