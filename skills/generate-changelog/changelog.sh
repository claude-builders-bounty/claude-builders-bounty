#!/usr/bin/env bash
# Cross-platform wrapper — delegates to changelog.py when bash mapfile is unavailable.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$DIR/changelog.py" "$@"
