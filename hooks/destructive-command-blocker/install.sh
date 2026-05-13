#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${HOOK_DIR}"
cp "${SCRIPT_DIR}/destructive_command_blocker.py" "${HOOK_DIR}/destructive_command_blocker.py"
chmod +x "${HOOK_DIR}/destructive_command_blocker.py"
touch "${HOOK_DIR}/blocked.log"

echo "Installed Claude Code hook at ${HOOK_DIR}/destructive_command_blocker.py"
echo "Add it as a PreToolUse Bash hook in your Claude Code hooks settings."
