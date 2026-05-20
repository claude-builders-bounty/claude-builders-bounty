#!/usr/bin/env python3
"""Install Claude Code settings for the destructive Bash guard hook."""

from __future__ import annotations

import json
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python ~/.claude/hooks/block_destructive_bash.py"


def main() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    bash_entry = next(
        (entry for entry in pre_tool_use if entry.get("matcher") == "Bash"),
        None,
    )
    if bash_entry is None:
        bash_entry = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_entry)

    hook_config = {"type": "command", "command": HOOK_COMMAND}
    if hook_config not in bash_entry.setdefault("hooks", []):
        bash_entry["hooks"].append(hook_config)

    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Installed destructive Bash guard in {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
