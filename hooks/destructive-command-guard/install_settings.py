#!/usr/bin/env python3
"""Install the destructive command guard in ~/.claude/settings.json."""

from __future__ import annotations

import json
from pathlib import Path


HOOK_COMMAND = "~/.claude/hooks/destructive-command-guard.py"


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    claude_dir = Path.home() / ".claude"
    settings_path = claude_dir / "settings.json"
    claude_dir.mkdir(parents=True, exist_ok=True)

    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": HOOK_COMMAND,
            }
        ],
    }

    already_installed = any(
        item.get("matcher") == "Bash"
        and any(hook.get("command") == HOOK_COMMAND for hook in item.get("hooks", []))
        for item in pre_tool_use
    )

    if not already_installed:
        pre_tool_use.append(entry)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed destructive command guard in {settings_path}")


if __name__ == "__main__":
    main()
