#!/usr/bin/env python3
"""Install the destructive Bash blocker into Claude Code user settings."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_bash.py"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    bash_matcher = None
    for matcher in pre_tool_use:
        if matcher.get("matcher") == "Bash":
            bash_matcher = matcher
            break

    if bash_matcher is None:
        bash_matcher = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_matcher)

    bash_hooks = bash_matcher.setdefault("hooks", [])
    hook = {"type": "command", "command": HOOK_COMMAND}
    if hook not in bash_hooks:
        bash_hooks.append(hook)

    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed destructive Bash blocker in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
