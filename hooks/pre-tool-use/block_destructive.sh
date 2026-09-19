#!/usr/bin/env bash
# Claude Code pre-tool-use hook wrapper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/block_destructive.py" "$@"
