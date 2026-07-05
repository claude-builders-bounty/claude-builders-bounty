#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/hooks and settings."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "block-destructive-bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
TARGET_HOOK = HOOKS_DIR / "block-destructive-bash.py"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def hook_command() -> str:
    python = Path(sys.executable)
    return f'"{python}" "{TARGET_HOOK}"'


def install_hook_file() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    mode = TARGET_HOOK.stat().st_mode
    TARGET_HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_settings() -> None:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": hook_command()}],
    }

    for existing in pre_tool_use:
        if existing.get("matcher") == "Bash":
            commands = [
                hook.get("command")
                for hook in existing.get("hooks", [])
                if isinstance(hook, dict)
            ]
            if hook_command() in commands:
                break
    else:
        pre_tool_use.append(entry)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    install_hook_file()
    install_settings()
    print(f"Installed {TARGET_HOOK}")
    print(f"Updated {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
