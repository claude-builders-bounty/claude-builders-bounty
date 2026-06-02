#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SOURCE="${SCRIPT_DIR}/destructive-command-guard.py"
HOOK_TARGET="${HOOK_DIR}/destructive-command-guard.py"
SETTINGS_PATH="${HOME}/.claude/settings.json"

mkdir -p "${HOOK_DIR}"
cp "${HOOK_SOURCE}" "${HOOK_TARGET}"
chmod +x "${HOOK_TARGET}"

python3 - "${SETTINGS_PATH}" "${HOOK_TARGET}" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_target = sys.argv[2]

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{settings_path} is not valid JSON: {exc}") from exc
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_target,
        }
    ],
}

already_installed = any(
    group.get("matcher") == "Bash"
    and any(handler.get("command") == hook_target for handler in group.get("hooks", []))
    for group in pre_tool_use
)

if not already_installed:
    pre_tool_use.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive command guard at ${HOOK_TARGET}"
