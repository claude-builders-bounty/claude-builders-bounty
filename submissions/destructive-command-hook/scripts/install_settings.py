#!/usr/bin/env python3
"""Install the destructive-command blocker into Claude Code settings."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_commands.py"
HOOK_ENTRY = {"type": "command", "command": HOOK_COMMAND}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open(encoding="utf-8") as settings_file:
        return json.load(settings_file)


def main() -> int:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for entry in pre_tool_use:
        if entry.get("matcher") != "Bash":
            continue
        bash_hooks = entry.setdefault("hooks", [])
        if HOOK_ENTRY not in bash_hooks:
            bash_hooks.append(HOOK_ENTRY)
        break
    else:
        pre_tool_use.append({"matcher": "Bash", "hooks": [HOOK_ENTRY]})

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed destructive-command blocker in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
