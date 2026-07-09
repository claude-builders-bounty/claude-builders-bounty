#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SCRIPT_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/block_destructive_bash.py"
SCRIPT_TARGET="$HOOK_DIR/block_destructive_bash.py"

mkdir -p "$HOOK_DIR"
cp "$SCRIPT_SOURCE" "$SCRIPT_TARGET"
chmod +x "$SCRIPT_TARGET"

python3 - "$SETTINGS_FILE" "$SCRIPT_TARGET" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
script_path = Path(sys.argv[2]).expanduser().resolve()
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    data = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre_tool = hooks.setdefault("PreToolUse", [])
handler = {
    "type": "command",
    "command": "python3",
    "args": [str(script_path)],
    "timeout": 5,
}

group = None
for candidate in pre_tool:
    if candidate.get("matcher") == "Bash":
        group = candidate
        break

if group is None:
    group = {"matcher": "Bash", "hooks": []}
    pre_tool.append(group)

group_hooks = group.setdefault("hooks", [])
if handler not in group_hooks:
    group_hooks.append(handler)

settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive Bash command hook at $SCRIPT_TARGET"
echo "Updated Claude Code settings at $SETTINGS_FILE"