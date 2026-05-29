#!/usr/bin/env python3
"""Install the destructive Bash command guard into Claude Code settings."""

from __future__ import annotations

import json
import shutil
import stat
import sys
from pathlib import Path


HOOK_NAME = "block_destructive_bash.py"


def quote_command(path: Path) -> str:
    return f'"{sys.executable}" "{path}"'


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def save_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def install() -> Path:
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    source = Path(__file__).resolve().with_name(HOOK_NAME)
    target = hooks_dir / HOOK_NAME
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = claude_dir / "settings.json"
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    command = quote_command(target)
    already_registered = any(
        HOOK_NAME in hook.get("command", "")
        for entry in pre_tool_use
        for hook in entry.get("hooks", [])
        if isinstance(hook, dict)
    )

    if not already_registered:
        pre_tool_use.append(
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": command,
                    }
                ],
            }
        )

    save_settings(settings_path, settings)
    return target


def main() -> int:
    target = install()
    print(f"Installed destructive command hook at {target}")
    print("Claude Code PreToolUse/Bash hook is registered in ~/.claude/settings.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
