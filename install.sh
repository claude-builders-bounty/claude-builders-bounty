#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
HOOKS_DIR="${CLAUDE_DIR}/hooks"
SETTINGS_FILE="${CLAUDE_DIR}/settings.json"
HOOK_FILE="${HOOKS_DIR}/destructive_bash_guard.py"

mkdir -p "${HOOKS_DIR}"
cp "${REPO_DIR}/hooks/destructive_bash_guard.py" "${HOOK_FILE}"
chmod +x "${HOOK_FILE}"

SETTINGS_FILE="${SETTINGS_FILE}" HOOK_FILE="${HOOK_FILE}" python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
hook_file = os.environ["HOOK_FILE"]

if settings_path.exists():
    with settings_path.open(encoding="utf-8") as source:
        settings = json.load(source)
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_file,
        }
    ],
}

for existing in pre_tool_use:
    if existing == entry:
        break
else:
    pre_tool_use.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
with settings_path.open("w", encoding="utf-8") as target:
    json.dump(settings, target, indent=2)
    target.write("\n")
PY

echo "Installed destructive Bash guard hook at ${HOOK_FILE}"
echo "Claude Code PreToolUse configuration updated in ${SETTINGS_FILE}"
