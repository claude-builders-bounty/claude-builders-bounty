#!/usr/bin/env bash
# changelog.sh — one-command CHANGELOG generator.
# Usage: bash changelog.sh [--stdout] [--output FILE] [--since TAG] [--repo DIR]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/changelog.py" "$@"
