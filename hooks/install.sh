#!/usr/bin/env bash
# One-line installer for the destructive-bash hook.
#
#   curl -sSL https://.../install.sh | bash
#
# What it does:
#   1. Copies the hook script into ~/.claude/hooks/ and marks it executable.
#   2. Registers the hook in ~/.claude/settings.json so Claude Code calls it
#      on every PreToolUse event for the Bash tool.
#
# The script is idempotent: re-running replaces the hook file and merges the
# settings entry without creating duplicates.

set -euo pipefail

HOOK_SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/block-destructive.py"
HOOK_DST_DIR="${HOME}/.claude/hooks"
HOOK_DST="${HOOK_DST_DIR}/block-destructive.py"
SETTINGS_FILE="${HOME}/.claude/settings.json"

mkdir -p "${HOOK_DST_DIR}"
cp -f "${HOOK_SRC}" "${HOOK_DST}"
chmod +x "${HOOK_DST}"

if [ ! -f "${SETTINGS_FILE}" ]; then
  echo '{}' > "${SETTINGS_FILE}"
fi

python3 - "${SETTINGS_FILE}" "${HOOK_DST}" <<'PY'
import json, sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = sys.argv[2]

settings = json.loads(settings_path.read_text() or "{}")
hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# Drop any existing entries that point at the same hook path so the script
# is idempotent across re-runs.
pre[:] = [
    entry for entry in pre
    if not any(
        isinstance(h, dict) and h.get("command") == hook_path
        for h in entry.get("hooks", [])
    )
]

pre.append({
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"python3 {hook_path}",
        }
    ],
})

settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY

echo "✔ Installed hook at ${HOOK_DST}"
echo "✔ Registered PreToolUse matcher in ${SETTINGS_FILE}"
echo ""
echo "Try it: ask Claude to run 'rm -rf /tmp/should-fail'. The hook will"
echo "refuse and the attempt will be appended to ~/.claude/hooks/blocked.log."
