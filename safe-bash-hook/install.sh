#!/usr/bin/env bash
set -euo pipefail

hook_dir="${HOME}/.claude/hooks"
settings_path="${HOME}/.claude/settings.json"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$hook_dir"
cp "${script_dir}/block_destructive_bash.py" "${hook_dir}/block_destructive_bash.py"
chmod +x "${hook_dir}/block_destructive_bash.py"

python3 - "$settings_path" <<'PY'
import json
import os
import sys

settings_path = os.path.expanduser(sys.argv[1])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py",
        }
    ],
}

if os.path.exists(settings_path):
    with open(settings_path, "r", encoding="utf-8") as handle:
        try:
            settings = json.load(handle)
        except json.JSONDecodeError:
            raise SystemExit(f"Refusing to modify invalid JSON: {settings_path}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

def same_hook(item):
    return (
        item.get("matcher") == entry["matcher"]
        and item.get("hooks") == entry["hooks"]
    )

if not any(isinstance(item, dict) and same_hook(item) for item in pre_tool_use):
    pre_tool_use.append(entry)

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w", encoding="utf-8") as handle:
    json.dump(settings, handle, indent=2)
    handle.write("\n")
PY

echo "Installed safe Bash hook and updated ${settings_path}"
