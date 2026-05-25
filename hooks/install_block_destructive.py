#!/usr/bin/env python3
"""Install the destructive Bash guard into ~/.claude/hooks and settings.json."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path


HOOK_NAME = "block_destructive_bash.py"


def claude_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")).expanduser()


def command_for(hook_path: Path) -> str:
    return f'"{sys.executable}" "{hook_path}"'


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}
    with settings_path.open("r", encoding="utf-8") as settings_file:
        try:
            loaded = json.load(settings_file)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Cannot update invalid JSON in {settings_path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit(f"Cannot update {settings_path}: expected a JSON object")
    return loaded


def install_hook(settings: dict, hook_command: str) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": hook_command,
            }
        ],
    }

    for existing in pre_tool_use:
        if not isinstance(existing, dict):
            continue
        if existing.get("matcher") != "Bash":
            continue
        for hook in existing.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == hook_command:
                return False

    pre_tool_use.append(entry)
    return True


def main() -> int:
    config_dir = claude_dir()
    hooks_dir = config_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    source = Path(__file__).with_name(HOOK_NAME)
    target = hooks_dir / HOOK_NAME
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = config_dir / "settings.json"
    settings = load_settings(settings_path)
    changed = install_hook(settings, command_for(target))

    if changed or not settings_path.exists():
        with settings_path.open("w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file, indent=2)
            settings_file.write("\n")

    print(f"Installed {target}")
    print(f"Updated {settings_path}" if changed else f"Hook entry already present in {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
