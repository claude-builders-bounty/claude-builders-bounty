#!/usr/bin/env python3
"""Install the guard, preserving unrelated Claude Code settings and hooks."""
import json
from pathlib import Path
import shlex
import shutil
import sys


def install(root):
    settings = root / "settings.json"
    data = json.loads(settings.read_text()) if settings.exists() else {}
    if not isinstance(data, dict):
        raise ValueError("settings.json must be an object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks must be an object")
    entries = hooks.setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        raise ValueError("PreToolUse must be an array")
    destination = root / "hooks" / "jrcage-destructive-guard.py"
    command = shlex.quote(sys.executable) + " " + shlex.quote(str(destination))
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": command, "timeout": 10}]}
    if entry not in entries:
        entries.append(entry)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if settings.exists():
        backup = root / "settings.before-jrcage-guard.json"
        if not backup.exists():
            shutil.copy2(settings, backup)
    shutil.copyfile(Path(__file__).with_name("guard.py"), destination)
    destination.chmod(0o600)
    # Replace only after successfully parsing and preparing all settings.
    temporary = root / "settings.jrcage-guard.tmp"
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(data, output, indent=2)
        output.write("\n")
    temporary.chmod(0o600)
    temporary.replace(settings)
    return destination


if __name__ == "__main__":
    print("Installed:", install(Path.home() / ".claude"))
    print("Restart Claude Code and inspect /hooks to confirm the Bash matcher.")
