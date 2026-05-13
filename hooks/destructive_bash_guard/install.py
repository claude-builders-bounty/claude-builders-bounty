#!/usr/bin/env python3
"""Register the destructive Bash guard in Claude Code user settings."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_PATH = Path.home() / ".claude" / "hooks" / "destructive_bash_guard.py"
HOOK_ENTRY = {"type": "command", "command": str(HOOK_PATH)}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open(encoding="utf-8") as settings_file:
        return json.load(settings_file)


def main() -> int:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    bash_group = next((group for group in pre_tool_use if group.get("matcher") == "Bash"), None)
    if bash_group is None:
        bash_group = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_group)

    group_hooks = bash_group.setdefault("hooks", [])
    if not any(hook.get("command") == str(HOOK_PATH) for hook in group_hooks):
        group_hooks.append(HOOK_ENTRY)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Registered PreToolUse Bash guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
