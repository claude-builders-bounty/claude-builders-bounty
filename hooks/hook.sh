#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook: Block Destructive Commands
# Wrapper that calls the Python hook

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/safety_hook.py" < /dev/stdin
