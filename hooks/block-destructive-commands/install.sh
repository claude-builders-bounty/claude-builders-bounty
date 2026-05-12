#!/usr/bin/env sh
set -eu

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

mkdir -p "${HOOK_DIR}"
cp "${SCRIPT_DIR}/block_destructive_commands.py" "${HOOK_DIR}/block_destructive_commands.py"
chmod +x "${HOOK_DIR}/block_destructive_commands.py"

python3 - "${SETTINGS_FILE}" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text().strip():
    settings = json.loads(settings_path.read_text())
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py",
        }
    ],
}

if entry not in pre_tool_use:
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY

printf 'Installed block_destructive_commands.py and registered the Bash PreToolUse hook.\n'
