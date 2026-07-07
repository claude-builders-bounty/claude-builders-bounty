#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_PATH="${HOME}/.claude/settings.json"
HOOK_PATH="${HOOK_DIR}/destructive-command-guard.py"

mkdir -p "${HOOK_DIR}"
cp "${ROOT_DIR}/hooks/destructive-command-guard.py" "${HOOK_PATH}"
chmod +x "${HOOK_PATH}"

python3 - "${SETTINGS_PATH}" "${HOOK_PATH}" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = sys.argv[2]

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update invalid JSON at {settings_path}: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
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

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive command guard at {hook_path}")
print(f"Updated Claude Code settings at {settings_path}")
PY
