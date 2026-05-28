#!/usr/bin/env bash
set -euo pipefail

hook_dir="${HOME}/.claude/hooks"
settings_path="${HOME}/.claude/settings.json"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$hook_dir"
cp "$script_dir/block_destructive_bash.py" "$hook_dir/block_destructive_bash.py"
chmod +x "$hook_dir/block_destructive_bash.py"

python3 - "$settings_path" "$hook_dir/block_destructive_bash.py" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = Path(sys.argv[2])
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text(encoding="utf-8").strip():
    data = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre_tool = hooks.setdefault("PreToolUse", [])
command = f"python3 {hook_path}"

entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": command}],
}

for existing in pre_tool:
    if existing.get("matcher") != "Bash":
        continue
    existing_hooks = existing.setdefault("hooks", [])
    if not any(hook.get("command") == command for hook in existing_hooks):
        existing_hooks.append({"type": "command", "command": command})
    break
else:
    pre_tool.append(entry)

settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Installed hook and updated {settings_path}")
PY

