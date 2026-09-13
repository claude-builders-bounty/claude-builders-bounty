#!/usr/bin/env bash
# Wrapper so Claude Code can call the Python hook without hardcoding python path.
# Falls back to python if python3 missing. Exits 0/2 per Claude hook contract.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$DIR/block_destructive_bash.py"
else
  exec python "$DIR/block_destructive_bash.py"
fi
