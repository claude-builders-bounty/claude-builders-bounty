#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOOK_DIR" "$(dirname "$SETTINGS_FILE")"
install -m 755 "$SCRIPT_DIR/hooks/destructive_bash_guard.py" "$HOOK_DIR/destructive_bash_guard.py"

SETTINGS_FILE="$SETTINGS_FILE" python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
if settings_path.exists() and settings_path.read_text().strip():
    data = json.loads(settings_path.read_text())
else:
    data = {}

hook_entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_bash_guard.py",
        }
    ],
}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
exists = any(
    item.get("matcher") == "Bash"
    and any(h.get("command") == hook_entry["hooks"][0]["command"] for h in item.get("hooks", []))
    for item in pre
    if isinstance(item, dict)
)
if not exists:
    pre.append(hook_entry)

settings_path.write_text(json.dumps(data, indent=2) + "\n")
PY

printf 'Installed destructive Bash guard and registered it in %s\n' "$SETTINGS_FILE"
