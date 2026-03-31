#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SOURCE="${SCRIPT_DIR}/block_destructive_commands.py"
HOOK_DIR="${HOME}/.claude/hooks"
HOOK_TARGET="${HOOK_DIR}/block_destructive_commands.py"
SETTINGS_PATH="${HOME}/.claude/settings.json"

mkdir -p "${HOOK_DIR}"
cp "${HOOK_SOURCE}" "${HOOK_TARGET}"
chmod +x "${HOOK_TARGET}"

python3 - "${SETTINGS_PATH}" "${HOOK_TARGET}" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1]).expanduser()
hook_target = str(Path(sys.argv[2]).expanduser())

if settings_path.exists():
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    payload = {}

hooks = payload.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

target_entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_target,
        }
    ],
}

for entry in pre_tool_use:
    if not isinstance(entry, dict):
        continue
    if entry.get("matcher") != "Bash":
        continue
    existing_hooks = entry.setdefault("hooks", [])
    for hook in existing_hooks:
        if isinstance(hook, dict) and hook.get("type") == "command" and hook.get("command") == hook_target:
            break
    else:
        existing_hooks.append(target_entry["hooks"][0])
    break
else:
    pre_tool_use.append(target_entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed hook to ${HOOK_TARGET}"
echo "Updated ${SETTINGS_PATH}"
