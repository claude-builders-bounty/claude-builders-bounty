#!/usr/bin/env python3
"""Install the Destructive Bash Guard hook into ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_bash_guard.py"


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
            try:
                settings = json.load(settings_file)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {SETTINGS_PATH}: {exc}") from exc
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    bash_entry = None
    for entry in pre_tool_use:
        if isinstance(entry, dict) and entry.get("matcher") == "Bash":
            bash_entry = entry
            break

    if bash_entry is None:
        bash_entry = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_entry)

    hook_list = bash_entry.setdefault("hooks", [])
    if not any(
        isinstance(hook, dict)
        and hook.get("type") == "command"
        and hook.get("command") == HOOK_COMMAND
        for hook in hook_list
    ):
        hook_list.append({"type": "command", "command": HOOK_COMMAND})

    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed Destructive Bash Guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
