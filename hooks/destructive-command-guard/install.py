#!/usr/bin/env python3
"""Install the destructive command guard into project .claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path(".claude") / "settings.json"
HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ${CLAUDE_PROJECT_DIR}/hooks/destructive-command-guard/destructive_command_guard.py",
        }
    ],
}


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])
    if HOOK_ENTRY not in pre_tool:
        pre_tool.append(HOOK_ENTRY)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed destructive command guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

