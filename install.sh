#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
HOOK_FILE="$HOOK_DIR/block_hook.py"

mkdir -p "$HOOK_DIR"
install -m 0755 "$SOURCE_DIR/block_hook.py" "$HOOK_FILE"

HOOK_FILE="$HOOK_FILE" SETTINGS_FILE="$SETTINGS_FILE" python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
hook_file = os.environ["HOOK_FILE"]
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Refusing to overwrite invalid JSON in {settings_path}: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool = hooks.setdefault("PreToolUse", [])
command = f"python3 {hook_file}"

already_present = False
for group in pre_tool:
    if group.get("matcher") != "Bash":
        continue
    for hook in group.get("hooks", []):
        if hook.get("type") == "command" and hook.get("command") == command:
            already_present = True
            break

if not already_present:
    pre_tool.append(
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

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed hook: {hook_file}")
print(f"Updated settings: {settings_path}")
PY
