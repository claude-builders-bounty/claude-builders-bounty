#!/usr/bin/env bash
set -euo pipefail

hook_dir="${HOME}/.claude/hooks"
mkdir -p "${hook_dir}"
cp "$(dirname "$0")/block_destructive_bash.py" "${hook_dir}/block_destructive_bash.py"
chmod +x "${hook_dir}/block_destructive_bash.py"

cat <<'JSON'
Installed ~/.claude/hooks/block_destructive_bash.py

Add this to your Claude Code settings:

{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
JSON
