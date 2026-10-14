#!/usr/bin/env bash
# install.sh -- install the block-destructive PreToolUse hook for Claude Code.
#
#   1. copies block_destructive.py to ~/.claude/hooks/ (executable)
#   2. merges the PreToolUse/Bash wiring into ~/.claude/settings.json
#      (idempotent; backs the old file up to settings.json.bak first)
#
# Usage:  ./install.sh
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOME/.claude/hooks"
install -m 0755 "$DIR/block_destructive.py" "$HOME/.claude/hooks/block_destructive.py"
python3 "$DIR/install.py"

echo "Done. Blocked attempts will be logged to $HOME/.claude/hooks/blocked.log"
echo "Restart Claude Code (or start a new session) for the hook to take effect."
