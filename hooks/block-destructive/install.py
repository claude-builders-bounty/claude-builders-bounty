#!/usr/bin/env python3
"""Install the destructive-command blocker into ~/.claude/hooks."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "pre_tool_use.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOK_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOK_DIR / "block-destructive.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def command_for_hook() -> str:
    return f'"{sys.executable}" "{TARGET_HOOK}"'


def merge_settings(settings: dict) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])
    command = command_for_hook()
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            },
        ],
    }

    for existing in pre_tool:
        if existing.get("matcher") != "Bash":
            continue
        existing_hooks = existing.setdefault("hooks", [])
        if not any(hook.get("command") == command for hook in existing_hooks):
            existing_hooks.append(entry["hooks"][0])
        return settings

    pre_tool.append(entry)
    return settings


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(TARGET_HOOK.stat().st_mode | stat.S_IXUSR)

    settings = merge_settings(load_settings())
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed {TARGET_HOOK}")
    print(f"Updated {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
