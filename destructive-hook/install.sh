#!/usr/bin/env bash
# One-command installer for the destructive-command PreToolUse hook.
#
#   bash install.sh
#
# Copies the hook to ~/.claude/hooks/ and registers it in
# ~/.claude/settings.json (existing settings are preserved).
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="${HOME}/.claude/hooks"
SETTINGS="${HOME}/.claude/settings.json"

mkdir -p "${HOOKS_DIR}"
cp "${SRC_DIR}/scripts/destructive_hook.py" "${HOOKS_DIR}/destructive_hook.py"
chmod +x "${HOOKS_DIR}/destructive_hook.py"

python3 - "${HOOKS_DIR}" "${SETTINGS}" <<'PY'
import json, os, sys

hooks_dir, settings_path = sys.argv[1], sys.argv[2]
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"python3 {hooks_dir}/destructive_hook.py",
            "timeout": 5,
        }
    ],
}

if os.path.exists(settings_path):
    with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)
else:
    settings = {}

pre = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
if not any(
    "destructive_hook.py" in h.get("command", "")
    for block in pre
    for h in block.get("hooks", [])
):
    pre.append(entry)

with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
print(f"registered PreToolUse hook in {settings_path}")
PY

echo
echo "Installed. Every blocked command is logged to ${HOOKS_DIR}/blocked.log"
echo "Verify:  python3 ${SRC_DIR}/testcases/run_tests.py"
