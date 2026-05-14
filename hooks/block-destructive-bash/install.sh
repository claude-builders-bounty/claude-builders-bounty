#!/usr/bin/env bash
set -euo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hooks_dir="$HOME/.claude/hooks"
settings_file="$HOME/.claude/settings.json"
hook_file="$hooks_dir/block_destructive_bash.py"

mkdir -p "$hooks_dir"
cp "$source_dir/block_destructive_bash.py" "$hook_file"
chmod +x "$hook_file"
touch "$hooks_dir/blocked.log"

python_cmd="python3"
case "${OS:-}" in
  Windows_NT) python_cmd="python" ;;
esac

export SETTINGS_FILE="$settings_file"
export HOOK_FILE="$hook_file"
export PYTHON_CMD="$python_cmd"

"$python_cmd" <<'PY'
import json
import os
import shlex
from pathlib import Path

settings_path = Path(os.environ["SETTINGS_FILE"])
hook_file = os.environ["HOOK_FILE"]
python_cmd = os.environ["PYTHON_CMD"]
command = f"{shlex.quote(python_cmd)} {shlex.quote(hook_file)}"

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
      "command": command,
    }
  ],
}

def same_entry(candidate):
  if candidate.get("matcher") != "Bash":
    return False
  for hook in candidate.get("hooks", []):
    if hook.get("command") == command:
      return True
  return False

if not any(isinstance(candidate, dict) and same_entry(candidate) for candidate in pre_tool_use):
  pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
PY

cat <<EOF
Installed destructive Bash guard hook:
  $hook_file

Updated Claude Code settings:
  $settings_file

Restart Claude Code to reload hook settings.
EOF
