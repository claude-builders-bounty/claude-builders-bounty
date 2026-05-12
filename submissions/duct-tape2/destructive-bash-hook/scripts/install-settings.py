#!/usr/bin/env python3
"""Install the Bash blocker hook into ~/.claude/settings.json without clobbering other hooks."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = str(Path.home() / ".claude" / "hooks" / "block-destructive-bash.py")


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8") or "{}")
    else:
        data = {}

    hooks = data.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    group = None
    for item in pre_tool_use:
        if item.get("matcher") == "Bash":
            group = item
            break
    if group is None:
        group = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(group)

    handlers = group.setdefault("hooks", [])
    handler = {"type": "command", "command": HOOK_COMMAND}
    if not any(h.get("type") == "command" and h.get("command") == HOOK_COMMAND for h in handlers):
        handlers.append(handler)

    SETTINGS_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Installed PreToolUse Bash hook in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
