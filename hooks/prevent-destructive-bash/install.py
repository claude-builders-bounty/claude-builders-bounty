#!/usr/bin/env python3
"""Install the destructive Bash guard into Claude Code user settings."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


HOOK_DIR = Path.home() / ".claude" / "hooks"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
SOURCE_HOOK = Path(__file__).with_name("block_destructive_bash.py")
TARGET_HOOK = HOOK_DIR / "block_destructive_bash.py"
COMMAND = "python ~/.claude/hooks/block_destructive_bash.py"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def install_hook_file() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)
    TARGET_HOOK.chmod(0o755)


def install_settings() -> None:
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    hook_entry = {"type": "command", "command": COMMAND}
    matcher_entry = None
    for entry in pre_tool_use:
        if entry.get("matcher") == "Bash":
            matcher_entry = entry
            break

    if matcher_entry is None:
        pre_tool_use.append({"matcher": "Bash", "hooks": [hook_entry]})
    else:
        matcher_hooks = matcher_entry.setdefault("hooks", [])
        if hook_entry not in matcher_hooks:
            matcher_hooks.append(hook_entry)

    save_settings(settings)


def main() -> int:
    install_hook_file()
    install_settings()
    print(f"Installed hook: {TARGET_HOOK}")
    print(f"Updated settings: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
