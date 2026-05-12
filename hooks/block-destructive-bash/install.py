#!/usr/bin/env python3
"""Install the destructive Bash guard into the user's Claude Code settings."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


SOURCE_HOOK = Path(__file__).with_name("block_destructive_bash.py")
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def _load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{SETTINGS_PATH} must contain a JSON object")
    return data


def _write_settings(settings: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def _hook_handler(target_hook: Path) -> dict[str, Any]:
    return {
        "type": "command",
        "command": sys.executable,
        "args": [str(target_hook)],
    }


def _ensure_hook_config(settings: dict[str, Any], target_hook: Path) -> bool:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be a JSON object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise ValueError("settings.hooks.PreToolUse must be a JSON array")

    handler = _hook_handler(target_hook)
    for group in pre_tool_use:
        if not isinstance(group, dict) or group.get("matcher") != "Bash":
            continue
        group_hooks = group.setdefault("hooks", [])
        if not isinstance(group_hooks, list):
            raise ValueError("PreToolUse Bash group hooks must be a JSON array")
        if handler in group_hooks:
            return False
        group_hooks.append(handler)
        return True

    pre_tool_use.append({"matcher": "Bash", "hooks": [handler]})
    return True


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    target_hook = HOOKS_DIR / SOURCE_HOOK.name
    shutil.copy2(SOURCE_HOOK, target_hook)

    settings = _load_settings()
    changed = _ensure_hook_config(settings, target_hook)
    if changed or not SETTINGS_PATH.exists():
        _write_settings(settings)

    print(f"Installed hook: {target_hook}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
