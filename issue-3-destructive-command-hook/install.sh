#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$ROOT_DIR/destructive_guard.py" "$HOOK_DIR/destructive_guard.py"
chmod +x "$HOOK_DIR/destructive_guard.py"

python3 - "$SETTINGS" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
settings_path.parent.mkdir(parents=True, exist_ok=True)
if settings_path.exists():
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"Refusing to overwrite invalid JSON: {settings_path}")
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_guard.py",
        }
    ],
}

def is_ours(item):
    if not isinstance(item, dict):
        return False
    for hook in item.get("hooks", []):
        if isinstance(hook, dict) and "destructive_guard.py" in str(hook.get("command", "")):
            return True
    return False

pre[:] = [item for item in pre if not is_ours(item)]
pre.append(entry)
settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive Bash guard in $HOOK_DIR and registered PreToolUse matcher."
