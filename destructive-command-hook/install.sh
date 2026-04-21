#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${HOOK_DIR}" "${HOME}/.claude"
cp "${SCRIPT_DIR}/block_destructive_commands.py" "${HOOK_DIR}/block_destructive_commands.py"
chmod +x "${HOOK_DIR}/block_destructive_commands.py"

python3 - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = settings_path.with_suffix(".json.bak")
        backup.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
        settings = {}
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py",
        }
    ],
}

already_installed = any(
    item.get("matcher") == "Bash"
    and any(
        hook.get("command") == entry["hooks"][0]["command"]
        for hook in item.get("hooks", [])
        if isinstance(hook, dict)
    )
    for item in pre_tool_use
    if isinstance(item, dict)
)

if not already_installed:
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive command hook in {settings_path}")
PY
