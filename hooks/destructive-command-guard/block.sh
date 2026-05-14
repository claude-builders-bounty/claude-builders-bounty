#!/bin/bash
# Claude Code pre-tool-use hook — Block destructive commands
# Installed by: mkdir -p ~/.claude/hooks/pre_tool_use && ln -sf "$PWD/block.sh" ~/.claude/hooks/pre_tool_use/block.sh
# Requires: python3 (stdlib only — no pip packages needed)

DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/hook.py"
