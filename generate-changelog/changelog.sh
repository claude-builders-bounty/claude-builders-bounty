#!/usr/bin/env bash
# Generate CHANGELOG.md from git history.
# Usage: bash changelog.sh [SINCE_TAG] [OUTPUT_FILE]
# Examples:
#   bash changelog.sh             # auto-detect last tag
#   bash changelog.sh v1.2.0     # from specific tag
#   bash changelog.sh - -         # print to stdout, no file
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SINCE="${1:-}"
OUTPUT="${2:-CHANGELOG.md}"

python3 "$SCRIPT_DIR/changelog.py" \
  ${SINCE:+--since "$SINCE"} \
  ${OUTPUT:+--output "$OUTPUT"}
