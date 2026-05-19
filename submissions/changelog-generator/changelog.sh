#!/bin/bash
# changelog.sh — thin wrapper for changelog.py
# Usage: bash changelog.sh [--output FILE] [--tag TAG]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/changelog.py" "$@"
