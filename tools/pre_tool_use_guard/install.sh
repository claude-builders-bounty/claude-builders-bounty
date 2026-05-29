#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

HOOKS_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
HOOK_SCRIPT="${HOOKS_DIR}/pre_tool_use_guard.py"

mkdir -p "${HOOKS_DIR}"
cp "${ROOT_DIR}/pre_tool_use_guard.py" "${HOOK_SCRIPT}"
chmod +x "${HOOK_SCRIPT}"

python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.path.expanduser("~/.claude/settings.json"))
settings_path.parent.mkdir(parents=True, exist_ok=True)

try:
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
except Exception:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": os.path.expanduser("~/.claude/hooks/pre_tool_use_guard.py"),
        }
    ],
}

def same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

if not any(same(item, entry) for item in pre):
    pre.insert(0, entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Updated {settings_path}")
PY

echo "Installed hook to ${HOOK_SCRIPT}"
echo "Blocked attempts will be appended to ${HOME}/.claude/hooks/blocked.log"

