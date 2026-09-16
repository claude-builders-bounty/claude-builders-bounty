#!/usr/bin/env bash
# Install the PreToolUse destructive-command blocker for Claude Code.
# Usage: bash install.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="${HOME}/.claude/hooks"
HOOK_PATH="${HOOKS_DIR}/block_destructive.py"
SETTINGS="${HOME}/.claude/settings.json"

mkdir -p "${HOOKS_DIR}"
cp "${SRC_DIR}/block_destructive.py" "${HOOK_PATH}"
chmod +x "${HOOK_PATH}"

python3 - "$SETTINGS" "$HOOK_PATH" <<'PY'
import json, os, sys

settings_path, hook_path = sys.argv[1], sys.argv[2]
hook_command = f"python3 {hook_path}"

settings = {}
if os.path.exists(settings_path):
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception:
        print(f"WARNING: could not parse {settings_path}; leaving it untouched.", file=sys.stderr)
        sys.exit(1)

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

already = any(
    hook_path in (h.get("command") or "")
    for entry in pre
    for h in (entry.get("hooks") or [])
)
if not already:
    pre.append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": hook_command}],
    })

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
print("Installed hook and registered it in settings.json.")
PY
