#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
HOOK_PATH="${HOOK_DIR}/block-dangerous-bash.py"
SETTINGS_PATH="${HOME}/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/hooks/block-dangerous-bash.py" "$HOOK_PATH"
chmod +x "$HOOK_PATH"

HOOK_PATH="$HOOK_PATH" SETTINGS_PATH="$SETTINGS_PATH" python3 - <<'PY'
import json
import os
from pathlib import Path

hook_path = os.environ["HOOK_PATH"]
settings_path = Path(os.environ["SETTINGS_PATH"])
settings_path.parent.mkdir(parents=True, exist_ok=True)
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
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
            "command": hook_path,
            "args": [],
        }
    ],
}

def is_same_entry(item):
    return any(hook.get("command") == hook_path for hook in item.get("hooks", []))

pre_tool_use[:] = [item for item in pre_tool_use if not is_same_entry(item)]
pre_tool_use.append(entry)
settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")
print(f"installed_hook={hook_path}")
print(f"updated_settings={settings_path}")
PY
