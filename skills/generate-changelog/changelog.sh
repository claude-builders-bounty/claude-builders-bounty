#!/usr/bin/env bash
# Thin wrapper so `bash changelog.sh` works per the bounty spec.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python)"
exec "$PY" "$DIR/changelog.py" "$@"
