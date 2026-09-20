#!/usr/bin/env python3
"""Install the destructive-command guard without clobbering Claude settings."""
import json
import shutil
import sys
from pathlib import Path

source_hook = Path(__file__).with_name("destructive_command_guard.py")
claude_dir = Path.home() / ".claude"
hook_dir = claude_dir / "hooks"
hook_path = hook_dir / "destructive_command_guard.py"
settings = claude_dir / "settings.json"

if not source_hook.is_file():
    raise SystemExit(f"Missing hook source: {source_hook}")

hook_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(source_hook, hook_path)

try:
    data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
except json.JSONDecodeError as exc:
    raise SystemExit(f"Refusing to overwrite invalid {settings}: {exc}")

if not isinstance(data, dict):
    raise SystemExit(f"Refusing to overwrite {settings}: top-level JSON must be an object.")

hooks_root = data.setdefault("hooks", {})
if not isinstance(hooks_root, dict):
    raise SystemExit(f"Refusing to modify {settings}: 'hooks' must be an object.")

pre_tool_use = hooks_root.setdefault("PreToolUse", [])
if not isinstance(pre_tool_use, list):
    raise SystemExit(f"Refusing to modify {settings}: hooks.PreToolUse must be a list.")

entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": sys.executable,
            "args": [str(hook_path)],
        }
    ],
}

if entry not in pre_tool_use:
    pre_tool_use.append(entry)

settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Installed hook at {hook_path}")
print(f"Updated Claude Code settings at {settings}")
