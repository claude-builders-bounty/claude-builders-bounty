#!/usr/bin/env python3
"""Install the destructive Bash blocker into ~/.claude/hooks."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path
from typing import Any


HOOK_NAME = "block-destructive-bash.py"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        data = json.load(settings_file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def ensure_pre_tool_use_hook(settings: dict[str, Any], command: str) -> None:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be an object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise ValueError("settings.hooks.PreToolUse must be a list")

    handler = {"type": "command", "command": command}

    for group in pre_tool_use:
        if not isinstance(group, dict):
            continue
        if group.get("matcher") != "Bash":
            continue
        configured_hooks = group.setdefault("hooks", [])
        if not isinstance(configured_hooks, list):
            raise ValueError("PreToolUse group hooks must be a list")
        if handler not in configured_hooks:
            configured_hooks.append(handler)
        return

    pre_tool_use.append({"matcher": "Bash", "hooks": [handler]})


def main() -> int:
    source_dir = Path(__file__).resolve().parent
    source_hook = source_dir / HOOK_NAME
    if not source_hook.exists():
        raise FileNotFoundError(source_hook)

    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    destination_hook = hooks_dir / HOOK_NAME

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_hook, destination_hook)
    destination_hook.chmod(destination_hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings = load_settings(settings_path)
    ensure_pre_tool_use_hook(settings, str(destination_hook))

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed {destination_hook}")
    print(f"Updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
