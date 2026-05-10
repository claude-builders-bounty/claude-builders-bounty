#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SOURCE="$SOURCE_DIR/block_destructive_commands.py"
HOOK_TARGET="$HOOK_DIR/block_destructive_commands.py"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

python3 - "$SETTINGS_FILE" "$HOOK_TARGET" <<'PY'
import json
import shlex
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = Path(sys.argv[2])

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
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
            "command": f"python3 {shlex.quote(str(hook_path))}",
        }
    ],
}

exists = any(
    hook.get("matcher") == entry["matcher"]
    and any(
        nested.get("command") == entry["hooks"][0]["command"]
        for nested in hook.get("hooks", [])
    )
    for hook in pre_tool_use
    if isinstance(hook, dict)
)

if not exists:
    pre_tool_use.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive command hook to $HOOK_TARGET"
echo "Updated Claude Code settings at $SETTINGS_FILE"
