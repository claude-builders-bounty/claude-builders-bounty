#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
HOOK_DIR="$CONFIG_DIR/hooks"
HOOK_PATH="$HOOK_DIR/block-destructive-bash.py"
SETTINGS_PATH="$CONFIG_DIR/settings.json"
SOURCE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

mkdir -p "$HOOK_DIR"
cp "$SOURCE_DIR/block-destructive-bash.py" "$HOOK_PATH"
chmod 700 "$HOOK_PATH"

python3 - "$SETTINGS_PATH" <<'PY'
import json
import os
import sys
import tempfile
from pathlib import Path

settings_path = Path(sys.argv[1])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update invalid JSON: {settings_path}: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-bash.py",
            "timeout": 5,
        }
    ],
}

already_installed = any(
    isinstance(item, dict)
    and item.get("matcher") == "Bash"
    and any(
        isinstance(hook, dict)
        and "block-destructive-bash.py" in str(hook.get("command", ""))
        for hook in item.get("hooks", [])
    )
    for item in pre_tool_use
)
if not already_installed:
    pre_tool_use.append(entry)

with tempfile.NamedTemporaryFile(
    "w", encoding="utf-8", dir=str(settings_path.parent), delete=False
) as handle:
    json.dump(settings, handle, indent=2)
    handle.write("\n")
    temporary_path = Path(handle.name)

temporary_path.replace(settings_path)
print(f"Installed hook: {settings_path.parent / 'hooks' / 'block-destructive-bash.py'}")
print(f"Updated settings: {settings_path}")
PY
