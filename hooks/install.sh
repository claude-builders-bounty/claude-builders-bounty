#!/usr/bin/env bash
# Install the Claude Code PreToolUse destructive bash blocker hook into ~/.claude/
set -euo pipefail

HOOKS_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${HOOKS_DIR}"
cp "${SCRIPT_DIR}/block-destructive-bash.py" "${HOOKS_DIR}/block-destructive-bash.py"
chmod +x "${HOOKS_DIR}/block-destructive-bash.py"

python3 - "${SETTINGS_FILE}" "${HOOKS_DIR}/block-destructive-bash.py" <<'PYEOF'
import json, os, sys
settings_path, hook_script = sys.argv[1], sys.argv[2]
data = {}
if os.path.exists(settings_path):
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

hooks = data.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
hook_cmd = f"python3 {hook_script}"

already_installed = any(
    entry.get("matcher") == "Bash"
    and any(h.get("command") == hook_cmd for h in entry.get("hooks", []))
    for entry in pre_tool_use
    if isinstance(entry, dict)
)

if not already_installed:
    pre_tool_use.append({
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": hook_cmd
            }
        ]
    })

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF

echo "Installed PreToolUse hook to ${HOOKS_DIR}/block-destructive-bash.py and registered in ${SETTINGS_FILE}"
