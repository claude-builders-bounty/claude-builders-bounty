#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${HOOK_DIR}/pre_tool_use_destructive_guard.py"

mkdir -p "${HOOK_DIR}"
cp "${SOURCE_DIR}/pre_tool_use_destructive_guard.py" "${TARGET}"
chmod +x "${TARGET}"

SETTINGS_FILE="${SETTINGS_FILE}" TARGET="${TARGET}" python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
target = os.environ["TARGET"]
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = settings_path.with_suffix(settings_path.suffix + ".bak")
        settings_path.replace(backup)
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
            "command": target,
            "timeout": 5,
        }
    ],
}

def same_entry(candidate):
    if candidate.get("matcher") != "Bash":
        return False
    for hook in candidate.get("hooks", []):
        if hook.get("command") == target:
            return True
    return False

if not any(isinstance(item, dict) and same_entry(item) for item in pre_tool_use):
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive command guard at ${TARGET}"
echo "Updated Claude Code settings at ${SETTINGS_FILE}"
