#!/usr/bin/env python3
"""Install the destructive command hook into ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


HOME = Path.home()
SETTINGS_PATH = HOME / ".claude" / "settings.json"
HOOK_COMMAND = str(HOME / ".claude" / "hooks" / "pre_tool_use_blocker.py")


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    if not any(existing == entry for existing in pre_tool_use):
        pre_tool_use.append(entry)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed PreToolUse Bash hook in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

