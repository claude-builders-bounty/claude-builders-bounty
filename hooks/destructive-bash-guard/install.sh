#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET_HOOK="${HOOK_DIR}/destructive-bash-guard.py"

mkdir -p "${HOOK_DIR}"
install -m 0755 "${SCRIPT_DIR}/pre_tool_use.py" "${TARGET_HOOK}"

python3 - "$SETTINGS_FILE" "$TARGET_HOOK" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = sys.argv[2]
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    backup_path = settings_path.with_suffix(settings_path.suffix + ".bak")
    backup_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_path,
        }
    ],
}

already_installed = any(
    group.get("matcher") == "Bash"
    and any(hook.get("command") == hook_path for hook in group.get("hooks", []))
    for group in pre_tool_use
    if isinstance(group, dict)
)
if not already_installed:
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive Bash guard at ${TARGET_HOOK}"
echo "Updated Claude Code settings at ${SETTINGS_FILE}"
