#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

mkdir -p "${HOOK_DIR}"
cp "${REPO_ROOT}/hooks/pre_tool_use_blocker.py" "${HOOK_DIR}/pre_tool_use_blocker.py"
chmod +x "${HOOK_DIR}/pre_tool_use_blocker.py"

cat <<'MSG'
Installed ~/.claude/hooks/pre_tool_use_blocker.py

Add this hook to your Claude Code settings:
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use_blocker.py" }
        ]
      }
    ]
  }
}
MSG
