#!/usr/bin/env bash
# Thin launcher so Claude Code can invoke the hook as a shell command.
# Forwards stdin JSON to block_destructive.py (stdlib Python 3).
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/block_destructive.py"
