#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_PATH="$HOOK_DIR/block_destructive_bash.py"
SETTINGS_PATH="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$(dirname "$0")/hooks/block_destructive_bash.py" "$HOOK_PATH"
chmod +x "$HOOK_PATH"

python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
hook_path = str(Path.home() / ".claude" / "hooks" / "block_destructive_bash.py")
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
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

if entry not in pre_tool_use:
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive Bash blocker hook at {hook_path}")
print(f"Updated Claude Code settings at {settings_path}")
PY
