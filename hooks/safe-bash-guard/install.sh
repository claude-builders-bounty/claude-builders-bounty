#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOOK_DIR"
cp "$SOURCE_DIR/safe_bash_guard.py" "$HOOK_DIR/safe_bash_guard.py"
chmod +x "$HOOK_DIR/safe_bash_guard.py"

python3 - "$SETTINGS_FILE" <<'PY'
import json
import os
import sys

settings_path = os.path.expanduser(sys.argv[1])
os.makedirs(os.path.dirname(settings_path), exist_ok=True)

if os.path.exists(settings_path) and os.path.getsize(settings_path) > 0:
    with open(settings_path, "r", encoding="utf-8") as handle:
        settings = json.load(handle)
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/safe_bash_guard.py",
        }
    ],
}

def same_hook(candidate):
    if candidate.get("matcher") != entry["matcher"]:
        return False
    return any(
        hook.get("type") == "command"
        and hook.get("command") == "python3 ~/.claude/hooks/safe_bash_guard.py"
        for hook in candidate.get("hooks", [])
    )

if not any(same_hook(candidate) for candidate in pre_tool_use):
    pre_tool_use.append(entry)

with open(settings_path, "w", encoding="utf-8") as handle:
    json.dump(settings, handle, indent=2)
    handle.write("\n")
PY

echo "Installed safe_bash_guard.py and updated $SETTINGS_FILE"
