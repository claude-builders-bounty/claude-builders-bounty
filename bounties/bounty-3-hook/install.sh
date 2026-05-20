#!/usr/bin/env bash
# install.sh — Install the Claude Code destructive-command hook
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SRC="${SCRIPT_DIR}/claude-code-hook.py"
CLAUDE_DIR="${HOME}/.claude"
HOOK_DST="${CLAUDE_DIR}/hooks"

mkdir -p "${HOOK_DST}"
cp "${HOOK_SRC}" "${HOOK_DST}/pre-tool-use"

chmod +x "${HOOK_DST}/pre-tool-use"

echo "✅ Hook installed at ${HOOK_DST}/pre-tool-use"
echo "   Claude Code will now auto-block destructive commands."
echo ""
echo "   To bypass: export CLAUDE_ALLOW_DESTRUCTIVE=1"
echo "   Log file: ${CLAUDE_DIR}/blocked_commands.log"
