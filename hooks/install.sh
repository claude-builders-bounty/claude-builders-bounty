#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${HOOK_DIR}"
install -m 0755 "${SCRIPT_DIR}/destructive-command-guard.py" "${HOOK_DIR}/destructive-command-guard.py"

cat <<'MSG'
Installed ~/.claude/hooks/destructive-command-guard.py

Add this PreToolUse hook to your Claude Code settings:

{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
MSG
