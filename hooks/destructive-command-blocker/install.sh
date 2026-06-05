#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/block_destructive_commands.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/block_destructive_commands.py" "$HOOK_FILE"
chmod +x "$HOOK_FILE"

python3 - "$SETTINGS_FILE" "$HOOK_FILE" <<'PY'
import json
import sys
from pathlib import Path

settings_file = Path(sys.argv[1])
hook_file = Path(sys.argv[2])
hook_command = f"python3 {hook_file}"

if settings_file.exists():
    settings = json.loads(settings_file.read_text(encoding="utf-8"))
else:
    settings = {}

pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_command,
        }
    ],
}

already_installed = any(
    candidate.get("matcher") == "Bash"
    and any(hook.get("command") == hook_command for hook in candidate.get("hooks", []))
    for candidate in pre_tool_use
)

if not already_installed:
    pre_tool_use.append(entry)

settings_file.parent.mkdir(parents=True, exist_ok=True)
settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive command blocker hook at $HOOK_FILE"
