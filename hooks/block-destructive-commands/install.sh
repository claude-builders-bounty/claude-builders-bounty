#!/usr/bin/env bash
# Install block-destructive-commands into ~/.claude/hooks (2-command setup).
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
SRC="$(cd "$(dirname "$0")" && pwd)/pre-tool-use.py"
DEST="$HOOK_DIR/pre-tool-use.py"

mkdir -p "$HOOK_DIR"
cp "$SRC" "$DEST"
chmod +x "$DEST"

python3 - "$SETTINGS" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    config = json.loads(settings_path.read_text())
else:
    config = {}

hooks = config.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use.py",
        }
    ],
}

def is_ours(item: dict) -> bool:
    if item.get("matcher") != "Bash":
        return False
    for hook in item.get("hooks", []):
        command = hook.get("command", "")
        if "pre-tool-use.py" in command:
            return True
    return False

hooks["PreToolUse"] = [item for item in pre_tool_use if not is_ours(item)]
hooks["PreToolUse"].append(entry)

settings_path.write_text(json.dumps(config, indent=2) + "\n")
print(f"Installed hook to {settings_path}")
PY
