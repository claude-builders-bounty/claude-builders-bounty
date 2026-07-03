#!/usr/bin/env python3
"""Install the destructive Bash blocker into ~/.claude/hooks."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_bash.py"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def install() -> Path:
    source = Path(__file__).with_name("block_destructive_bash.py")
    hook_dir = Path.home() / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    target = hook_dir / "block_destructive_bash.py"
    shutil.copy2(source, target)

    settings_path = Path.home() / ".claude" / "settings.json"
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    already_installed = any(
        hook.get("matcher") == "Bash"
        and any(
            item.get("type") == "command" and item.get("command") == HOOK_COMMAND
            for item in hook.get("hooks", [])
        )
        for hook in pre_tool_use
    )
    if not already_installed:
        pre_tool_use.append(entry)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    return settings_path


if __name__ == "__main__":
    path = install()
    print(f"Installed block_destructive_bash.py and updated {path}")
