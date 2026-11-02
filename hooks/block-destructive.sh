#!/usr/bin/env bash
# Claude Code PreToolUse Hook: Destructive Command Interceptor
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/block_destructive.py" "$@"
