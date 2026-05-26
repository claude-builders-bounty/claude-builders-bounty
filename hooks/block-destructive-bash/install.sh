#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"

mkdir -p "${HOOK_DIR}"
cp "${SCRIPT_DIR}/block_destructive_bash.py" "${HOOK_DIR}/block_destructive_bash.py"
chmod +x "${HOOK_DIR}/block_destructive_bash.py"

python3 - "$SETTINGS_FILE" "$HOOK_DIR/block_destructive_bash.py" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1]).expanduser()
hook_path = sys.argv[2]

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"Refusing to overwrite invalid JSON: {settings_path}")
else:
    settings = {}

settings.setdefault("hooks", {})
pre_tool = settings["hooks"].setdefault("PreToolUse", [])

entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_path,
        }
    ],
}

def same_entry(existing):
    return (
        existing.get("matcher") == "Bash"
        and any(hook.get("command") == hook_path for hook in existing.get("hooks", []))
    )

if not any(same_entry(existing) for existing in pre_tool):
    pre_tool.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive Bash guard in {settings_path}")
PY
