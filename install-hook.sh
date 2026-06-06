#!/bin/bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
HOOK_PATH="$HOOK_DIR/block_destructive_bash.py"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$HOOK_DIR"
cp "$SOURCE_DIR/hooks/block_destructive_bash.py" "$HOOK_PATH"
chmod +x "$HOOK_PATH"

HOOK_PATH="$HOOK_PATH" SETTINGS_FILE="$SETTINGS_FILE" python3 <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
hook_path = os.environ["HOOK_PATH"]
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    with settings_path.open("r", encoding="utf-8") as handle:
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
            "command": hook_path,
        }
    ],
}

for existing in pre_tool_use:
    if existing.get("matcher") == "Bash":
        existing_hooks = existing.setdefault("hooks", [])
        if not any(item.get("command") == hook_path for item in existing_hooks):
            existing_hooks.append(entry["hooks"][0])
        break
else:
    pre_tool_use.append(entry)

with settings_path.open("w", encoding="utf-8") as handle:
    json.dump(settings, handle, indent=2)
    handle.write("\n")
PY

echo "Installed destructive command hook: $HOOK_PATH"
echo "Updated Claude Code settings: $SETTINGS_FILE"
