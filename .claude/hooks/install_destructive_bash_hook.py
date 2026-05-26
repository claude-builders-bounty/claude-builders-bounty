#!/usr/bin/env python3
"""Install the destructive Bash guard into the user's Claude Code hooks."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"
HOOK_COMMAND = f"python ~/.claude/hooks/{HOOK_NAME}"


def claude_dir() -> Path:
    return Path.home() / ".claude"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")

    return data


def install_hook_file() -> None:
    source = Path(__file__).resolve().with_name(HOOK_NAME)
    target_dir = claude_dir() / "hooks"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_dir / HOOK_NAME)


def merge_hook_settings(settings: dict[str, Any]) -> dict[str, Any]:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for matcher in pre_tool_use:
        if not isinstance(matcher, dict):
            continue
        if matcher.get("matcher") != "Bash":
            continue

        handlers = matcher.setdefault("hooks", [])
        if any(isinstance(handler, dict) and handler.get("command") == HOOK_COMMAND for handler in handlers):
            return settings

        handlers.append({"type": "command", "command": HOOK_COMMAND})
        return settings

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": HOOK_COMMAND,
                }
            ],
        }
    )
    return settings


def install_settings() -> Path:
    settings_path = claude_dir() / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = merge_hook_settings(load_settings(settings_path))

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    return settings_path


def main() -> int:
    install_hook_file()
    settings_path = install_settings()
    print(f"Installed {HOOK_NAME} and updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
