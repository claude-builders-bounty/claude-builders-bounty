#!/usr/bin/env bash
# Wrapper for acceptance: bash changelog.sh
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/changelog.py" "$@"
