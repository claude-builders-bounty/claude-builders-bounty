#!/usr/bin/env sh
set -eu

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
HOOK_SOURCE="${REPO_DIR}/hooks/block_destructive_commands.py"
HOOK_TARGET="${HOOK_DIR}/block_destructive_commands.py"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod 755 "$HOOK_TARGET"

python3 - "$SETTINGS_FILE" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1]).expanduser()
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
hook_entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py",
        }
    ],
}

exists = any(
    entry.get("matcher") == hook_entry["matcher"]
    and hook_entry["hooks"][0] in entry.get("hooks", [])
    for entry in pre_tool_use
    if isinstance(entry, dict)
)
if not exists:
    pre_tool_use.append(hook_entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

printf 'Installed destructive command blocker in %s\n' "$HOOK_TARGET"
