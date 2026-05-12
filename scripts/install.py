#!/usr/bin/env python3
"""Install the destructive Bash command blocker for Claude Code."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / "hooks" / "block_destructive_bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
INSTALLED_HOOK = HOOKS_DIR / "block_destructive_bash.py"


def read_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def ensure_hook_config(settings: dict) -> dict:
    command = str(INSTALLED_HOOK)
    hook = {"type": "command", "command": command}
    group = {"matcher": "Bash", "hooks": [hook]}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for existing_group in pre_tool_use:
        if existing_group.get("matcher") != "Bash":
            continue
        existing_hooks = existing_group.setdefault("hooks", [])
        if not any(item.get("command") == command for item in existing_hooks):
            existing_hooks.append(hook)
        return settings

    pre_tool_use.append(group)
    return settings


def main() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, INSTALLED_HOOK)
    INSTALLED_HOOK.chmod(INSTALLED_HOOK.stat().st_mode | stat.S_IXUSR)

    settings = ensure_hook_config(read_settings())
    write_settings(settings)

    print(f"Installed hook: {INSTALLED_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    print(f"Blocked attempts will be logged to: {HOOKS_DIR / 'blocked.log'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
