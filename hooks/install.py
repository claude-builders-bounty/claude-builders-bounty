#!/usr/bin/env python3
"""Install and register the destructive-command Claude Code hook."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys


HOOK_NAME = "block_destructive_commands.py"


def install(home: Path | None = None) -> Path:
    home = home or Path.home()
    claude_dir = home / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    destination = hooks_dir / HOOK_NAME
    source = Path(__file__).with_name(HOOK_NAME)
    shutil.copy2(source, destination)

    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        with settings_path.open(encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    else:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError(f"{settings_path} must contain a JSON object")

    command = f'"{sys.executable}" "{destination}"'
    registration = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": command}],
    }

    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("The settings 'hooks' value must be an object")
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise ValueError("The settings 'hooks.PreToolUse' value must be an array")

    already_installed = any(
        entry.get("matcher") == "Bash"
        and any(
            HOOK_NAME in hook.get("command", "")
            for hook in entry.get("hooks", [])
            if isinstance(hook, dict)
        )
        for entry in pre_tool_use
        if isinstance(entry, dict)
    )
    if not already_installed:
        pre_tool_use.append(registration)

    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    return destination


def main() -> int:
    destination = install()
    print(f"Installed Claude Code hook at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
