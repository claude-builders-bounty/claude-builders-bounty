#!/usr/bin/env bash
# One-command installer for the pre-tool-use hook
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOOK_DIR"
cp "$SCRIPT_DIR/pre_tool_use.py" "$HOOK_DIR/"

# Install via claude CLI if available
if command -v claude &> /dev/null; then
  claude config set hooks.pre_tool_use "$HOOK_DIR/pre_tool_use.py"
  echo "✅ Installed. Hook active on next Claude Code session."
else
  echo "⚠️  Claude CLI not found. Manual step required:"
  echo "   claude config set hooks.pre_tool_use $HOOK_DIR/pre_tool_use.py"
fi
