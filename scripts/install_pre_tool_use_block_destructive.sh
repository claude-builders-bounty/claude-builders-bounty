#!/usr/bin/env bash
# install_pre_tool_use_block_destructive.sh
# One-command installer for the pre-tool-use block-destructive hook.
#
# Usage:  bash install_pre_tool_use_block_destructive.sh
# Effect: copies the hook to ~/.claude/hooks/ and registers it in
#         ~/.claude/settings.json under hooks.PreToolUse.
#
# Idempotent: re-running updates the entry instead of duplicating.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="${SCRIPT_DIR}/../hooks/pre-tool-use-block-destructive.py"
HOOK_DEST="${HOME}/.claude/hooks/pre-tool-use-block-destructive.py"
SETTINGS_FILE="${HOME}/.claude/settings.json"
PYTHON_BIN="$(command -v py || command -v python3 || command -v python || echo python)"

# 1. Copy hook
mkdir -p "${HOME}/.claude/hooks"
cp "${HOOK_SRC}" "${HOOK_DEST}"
chmod +x "${HOOK_DEST}"
echo "[install] copied hook to ${HOOK_DEST}"

# 2. Register in settings.json (preserves other settings)
mkdir -p "$(dirname "${SETTINGS_FILE}")"
if [ -f "${SETTINGS_FILE}" ]; then
    SETTINGS_BEFORE="${SETTINGS_FILE}.bak.$(date +%s)"
    cp "${SETTINGS_FILE}" "${SETTINGS_BEFORE}"
    echo "[install] backup of settings.json saved to ${SETTINGS_BEFORE}"
fi

HOOK_CMD="${PYTHON_BIN} ${HOOK_DEST}"

# Use python to safely merge JSON
"${PYTHON_BIN}" - "${SETTINGS_FILE}" "${HOOK_CMD}" <<'PYEOF'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_cmd = sys.argv[2]

if settings_path.exists():
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# Build new entry
new_entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": hook_cmd}],
}

# Idempotency: skip if command already registered
already = any(
    e.get("matcher") == "Bash" and any(
        h.get("command") == hook_cmd for h in e.get("hooks", [])
    )
    for e in pre
)

if not already:
    pre.append(new_entry)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"[install] registered hook in {settings_path}")
else:
    print(f"[install] hook already registered in {settings_path}, no changes")
PYEOF

echo "[install] DONE. Restart Claude Code to activate the hook."
