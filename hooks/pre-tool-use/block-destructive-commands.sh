#!/usr/bin/env bash
# Claude Code Pre-Tool-Use Hook Wrapper
# Intercepts dangerous bash commands before execution
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/block-destructive-commands.py" "$@"
