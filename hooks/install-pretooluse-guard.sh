#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/pre_tool_use_guard.py"
SCRIPT_TARGET="${HOOK_DIR}/pre_tool_use_guard.py"

detect_python() {
  if [[ -n "${PYTHON_BIN:-}" ]] && "${PYTHON_BIN}" --version >/dev/null 2>&1; then
    printf '%s\n' "${PYTHON_BIN}"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  if command -v py >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then
    printf 'py -3\n'
    return 0
  fi
  return 1
}

quote_arg() {
  printf '%q' "$1"
}

PYTHON_COMMAND="$(detect_python)" || {
  echo "Could not find Python. Set PYTHON_BIN=/path/to/python and rerun." >&2
  exit 1
}

mkdir -p "${HOOK_DIR}"
cp "${SCRIPT_SOURCE}" "${SCRIPT_TARGET}"
chmod +x "${SCRIPT_TARGET}"

if [[ "${PYTHON_COMMAND}" == "py -3" ]]; then
  HOOK_COMMAND="py -3 $(quote_arg "${SCRIPT_TARGET}")"
else
  HOOK_COMMAND="$(quote_arg "${PYTHON_COMMAND}") $(quote_arg "${SCRIPT_TARGET}")"
fi

${PYTHON_COMMAND} - "$SETTINGS_FILE" "$HOOK_COMMAND" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_command = sys.argv[2]

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise SystemExit(f"{settings_path} exists but is not valid JSON")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": hook_command,
        }
    ],
}

if entry not in pre_tool_use:
    pre_tool_use.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed PreToolUse guard at ${SCRIPT_TARGET}"
echo "Updated ${SETTINGS_FILE}"
