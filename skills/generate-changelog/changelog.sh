#!/usr/bin/env bash
set -e

# Run python changelog generator passing all forwarded arguments
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/generate_changelog.py" "$@"
