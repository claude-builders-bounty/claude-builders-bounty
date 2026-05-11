#!/usr/bin/env bash
set -euo pipefail

HOOKS_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_PATH="${HOOKS_DIR}/block_destructive_bash.py"
PYTHON_BIN="${PYTHON:-}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  elif command -v python.exe >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python.exe)"
  elif command -v py.exe >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v py.exe)"
  else
    echo "python3, python, python.exe, or py.exe is required to install the hook" >&2
    exit 1
  fi
fi

mkdir -p "${HOOKS_DIR}" "$(dirname "${SETTINGS_FILE}")"
cp "${SCRIPT_DIR}/hooks/block_destructive_bash.py" "${HOOK_PATH}"
chmod +x "${HOOK_PATH}"

PY_SETTINGS_FILE="${SETTINGS_FILE}"
PY_HOOK_PATH="${HOOK_PATH}"
HOOK_COMMAND_PATH="${HOOK_PATH}"
PYTHON_COMMAND="${PYTHON_BIN}"
HOOK_SHELL=""

if [[ "${PYTHON_BIN}" == *.exe ]] && command -v wslpath >/dev/null 2>&1; then
  PY_SETTINGS_FILE="$(wslpath -w "${SETTINGS_FILE}")"
  PY_HOOK_PATH="$(wslpath -w "${HOOK_PATH}")"
  HOOK_COMMAND_PATH="${PY_HOOK_PATH}"
  PYTHON_COMMAND="$(wslpath -w "${PYTHON_BIN}")"
  HOOK_SHELL="powershell"
elif [[ "${PYTHON_BIN}" == *.exe ]] && command -v cygpath >/dev/null 2>&1; then
  PY_SETTINGS_FILE="$(cygpath -w "${SETTINGS_FILE}")"
  PY_HOOK_PATH="$(cygpath -w "${HOOK_PATH}")"
  HOOK_COMMAND_PATH="${PY_HOOK_PATH}"
  PYTHON_COMMAND="$(cygpath -w "${PYTHON_BIN}")"
  HOOK_SHELL="powershell"
fi

"${PYTHON_BIN}" - "${PY_SETTINGS_FILE}" "${PY_HOOK_PATH}" "${PYTHON_COMMAND}" "${HOOK_COMMAND_PATH}" "${HOOK_SHELL}" <<'PY'
import json
import shlex
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = Path(sys.argv[2])
python_bin = sys.argv[3]
hook_command_path = sys.argv[4]
hook_shell = sys.argv[5]

if hook_shell == "powershell":
    def ps_quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    command = f"& {ps_quote(python_bin)} {ps_quote(hook_command_path)}"
else:
    command = f"{shlex.quote(python_bin)} {shlex.quote(hook_command_path)}"

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update invalid JSON in {settings_path}: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

target_group = None
for group in pre_tool_use:
    if group.get("matcher") == "Bash":
        target_group = group
        break

if target_group is None:
    target_group = {"matcher": "Bash", "hooks": []}
    pre_tool_use.append(target_group)

handlers = target_group.setdefault("hooks", [])
already_installed = any(
    "block_destructive_bash.py" in handler.get("command", "")
    for handler in handlers
    if isinstance(handler, dict)
)

if not already_installed:
    handler = {
        "type": "command",
        "command": command,
        "statusMessage": "Checking Bash command safety",
    }
    if hook_shell:
        handler["shell"] = hook_shell
    handlers.append(handler)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive Bash command hook at {hook_path}")
print(f"Updated Claude Code settings at {settings_path}")
PY
