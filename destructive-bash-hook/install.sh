#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SCRIPT_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/destructive_command_guard.py"
SCRIPT_TARGET="$HOOK_DIR/destructive_command_guard.py"

mkdir -p "$HOOK_DIR"
cp "$SCRIPT_SOURCE" "$SCRIPT_TARGET"
chmod +x "$SCRIPT_TARGET"

python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
hook_command = str(Path.home() / ".claude" / "hooks" / "destructive_command_guard.py")

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Refusing to overwrite invalid JSON in {settings_path}: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": hook_command}],
}

already_present = any(
    isinstance(item, dict)
    and item.get("matcher") == "Bash"
    and any(
        isinstance(hook, dict) and hook.get("command") == hook_command
        for hook in item.get("hooks", [])
    )
    for item in pre_tool_use
)

if not already_present:
    pre_tool_use.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed Claude Code PreToolUse destructive-command guard in {settings_path}")
PY
