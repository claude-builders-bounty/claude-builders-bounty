#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${HOOK_DIR}"
cp "${SCRIPT_DIR}/block_destructive_command.py" "${HOOK_DIR}/block_destructive_command.py"
chmod +x "${HOOK_DIR}/block_destructive_command.py"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "python3 or python is required to install this hook." >&2
  exit 1
fi

"${PYTHON_BIN}" - "$SETTINGS_FILE" "$PYTHON_BIN" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
python_bin = sys.argv[2]
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"{python_bin} ~/.claude/hooks/block_destructive_command.py",
        }
    ],
}

def same_entry(candidate):
    return (
        candidate.get("matcher") == entry["matcher"]
        and candidate.get("hooks") == entry["hooks"]
    )

if not any(same_entry(candidate) for candidate in pre_tool_use):
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

echo "Installed destructive command blocker hook."
