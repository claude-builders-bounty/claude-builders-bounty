#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

SOURCE = Path(__file__).with_name("block_destructive_bash.py")
HOOK_DIR = Path.home() / ".claude" / "hooks"
TARGET = HOOK_DIR / "block_destructive_bash.py"
SETTINGS = Path.home() / ".claude" / "settings.json"


def read_settings() -> dict:
    if not SETTINGS.exists():
        return {}
    with SETTINGS.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def write_settings(settings: dict) -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def hook_entry() -> dict:
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": f"python3 {TARGET}",
            }
        ],
    }


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    TARGET.chmod(0o755)

    settings = read_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"python3 {TARGET}"

    already_installed = any(
        inner.get("command") == command
        for group in pre_tool_use
        for inner in group.get("hooks", [])
    )
    if not already_installed:
        pre_tool_use.append(hook_entry())
        write_settings(settings)

    print(f"Installed hook: {TARGET}")
    print(f"Updated settings: {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
