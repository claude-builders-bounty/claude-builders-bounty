#!/usr/bin/env bash
# Claude Code PreToolUse Hook: Block Destructive Bash Commands
# Wrapper script — delegates to Python for pattern matching.
#
# Install (2 commands):
#   cp hooks/block-destructive/block-destructive.py ~/.claude/hooks/
#   cp hooks/block-destructive/block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
#
# Then add to ~/.claude/settings.json:
#   {
#     "hooks": {
#       "PreToolUse": [{
#         "matcher": "Bash",
#         "hooks": [{
#           "type": "command",
#           "command": "~/.claude/hooks/block-destructive.sh"
#         }]
#       }]
#     }
#   }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 &>/dev/null; then
    python3 "$SCRIPT_DIR/block-destructive.py"
elif command -v python &>/dev/null; then
    python "$SCRIPT_DIR/block-destructive.py"
else
    # No Python available — fail open
    exit 0
fi
