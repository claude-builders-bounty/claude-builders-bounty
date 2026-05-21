#!/usr/bin/env python3
"""Install the destructive Bash blocker into ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python ~/.claude/hooks/block_destructive_bash.py"
HOOK_ENTRY = {"type": "command", "command": HOOK_COMMAND}


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    if SETTINGS_PATH.exists():
        with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
            try:
                settings = json.load(settings_file)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Cannot update invalid JSON in {SETTINGS_PATH}: {exc}") from exc
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    bash_group = None
    for group in pre_tool_use:
        if group.get("matcher") == "Bash":
            bash_group = group
            break

    if bash_group is None:
        bash_group = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_group)

    group_hooks = bash_group.setdefault("hooks", [])
    if not any(hook.get("type") == "command" and hook.get("command") == HOOK_COMMAND for hook in group_hooks):
        group_hooks.append(HOOK_ENTRY)

    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed destructive Bash blocker in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
