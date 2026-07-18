#!/usr/bin/env python3
"""Install the hook and merge its current Claude Code settings entry."""

import json
import shutil
from pathlib import Path

source = Path(__file__).with_name("destructive_command_guard.py")
claude = Path.home() / ".claude"
hooks = claude / "hooks"
hooks.mkdir(parents=True, exist_ok=True)
target = hooks / source.name
shutil.copy2(source, target)
target.chmod(0o700)

settings_path = claude / "settings.json"
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
groups = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": str(target)}]}
if entry not in groups:
    groups.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"Installed {target} and updated {settings_path}")
