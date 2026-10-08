#!/usr/bin/env python3
"""Install quarry-guard.py and register it as a Claude Code PreToolUse hook."""

import json
import os
import shutil
from pathlib import Path

SOURCE = Path(__file__).with_name("quarry-guard.py")
HOOK_DIR = Path.home() / ".claude" / "hooks"
TARGET = HOOK_DIR / "quarry-guard.py"
SETTINGS = Path.home() / ".claude" / "settings.json"
COMMAND = "python3 ~/.claude/hooks/quarry-guard.py"


def main():
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(TARGET.stat().st_mode | 0o111)

    data = {}
    if SETTINGS.exists():
        try:
            data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raise SystemExit("Refusing to overwrite an unreadable ~/.claude/settings.json")

    if not isinstance(data, dict):
        raise SystemExit("Refusing to overwrite a non-object ~/.claude/settings.json")

    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    desired = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": COMMAND}],
    }

    already = any(
        isinstance(entry, dict)
        and any(
            isinstance(hook, dict) and hook.get("command") == COMMAND
            for hook in entry.get("hooks", [])
        )
        for entry in pre
    )
    if not already:
        pre.append(desired)

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    temp = SETTINGS.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, SETTINGS)
    print("Installed Claude Code destructive-command guard:", TARGET)


if __name__ == "__main__":
    main()
