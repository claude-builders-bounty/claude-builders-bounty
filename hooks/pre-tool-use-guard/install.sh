#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/.claude/hooks
cp "$(dirname "$0")/pre_tool_use_guard.py" ~/.claude/hooks/pre_tool_use_guard.py
chmod +x ~/.claude/hooks/pre_tool_use_guard.py
echo "✅ Installed Claude Code PreToolUse hook to ~/.claude/hooks/pre_tool_use_guard.py"
