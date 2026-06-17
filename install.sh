#!/usr/bin/env bash
set -euo pipefail

# install.sh — Install the destructive command hook for Claude Code
mkdir -p ~/.claude/hooks
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ln -sf "$SCRIPT_DIR/destructive-cmd-hook.py" ~/.claude/hooks/pre-tool-use
chmod +x "$SCRIPT_DIR/destructive-cmd-hook.py"
echo "Installed. Hook will run automatically on next Claude Code tool use."
echo "Blocked commands are logged to ~/.claude/hooks/blocked.log"
