#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
HOOK_PATH="$HOOK_DIR/destructive-command-guard.py"

mkdir -p "$HOOK_DIR"
cp "$SCRIPT_DIR/destructive-command-guard.py" "$HOOK_PATH"
chmod +x "$HOOK_PATH"

python3 - "$SETTINGS" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Refusing to modify invalid JSON in {settings_path}: {exc}")
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

command = 'python3 "$HOME/.claude/hooks/destructive-command-guard.py"'
already_present = False

for group in pre:
    if group.get("matcher") != "Bash":
        continue
    for handler in group.get("hooks", []):
        if "destructive-command-guard.py" in str(handler.get("command", "")):
            already_present = True
            break

if not already_present:
    pre.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                }
            ],
        }
    )

settings_path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"Installed hook and updated {settings_path}")
PY
