#!/usr/bin/env bash
# install.sh — install the destructive-bash hook into Claude Code's hooks dir.
#
# Two commands total:
#   bash install.sh
#   # then restart Claude Code
#
# Submission for claude-builders-bounty issue #3.

set -euo pipefail

DEST_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_NAME="block_destructive_bash.py"
HOOK_PATH="${DEST_DIR}/${SCRIPT_NAME}"

mkdir -p "${DEST_DIR}"

cp "$(dirname "$0")/${SCRIPT_NAME}" "${HOOK_PATH}"
chmod +x "${HOOK_PATH}"

echo "Installed hook script to ${HOOK_PATH}"

# Wire it into ~/.claude/settings.json under hooks.PreToolUse[].
# This is idempotent: if a matching command is already registered, do nothing.
python3 - "${SETTINGS_FILE}" "${HOOK_PATH}" <<'PY'
import json
import os
import sys
from pathlib import Path

settings_file = Path(sys.argv[1])
hook_path = sys.argv[2]
command_str = f"python3 {hook_path}"

settings = {}
if settings_file.exists():
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"WARN: {settings_file} is not valid JSON, leaving it alone.", file=sys.stderr)
        sys.exit(0)

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# Each entry is { "matcher": "Bash", "hooks": [{ "type": "command", "command": "..." }] }
already = False
for entry in pre:
    if entry.get("matcher") == "Bash":
        for h in entry.get("hooks", []):
            if h.get("command") == command_str:
                already = True
                break
        if not already:
            entry.setdefault("hooks", []).append({"type": "command", "command": command_str})
            already = True
        break

if not already:
    pre.append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": command_str}],
    })

settings_file.parent.mkdir(parents=True, exist_ok=True)
settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Wired hook into {settings_file} under hooks.PreToolUse")
PY

echo
echo "Done. Restart Claude Code (or start a new session) for the hook to take effect."
echo "Blocked attempts will be logged to ~/.claude/hooks/blocked.log."
