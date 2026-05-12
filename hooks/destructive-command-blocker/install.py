#!/usr/bin/env python3
"""Install the destructive command blocker hook for Claude Code."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_HOOK = SCRIPT_DIR / "destructive-command-blocker.py"


def main() -> int:
    claude_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")).expanduser()
    hook_dir = claude_dir / "hooks"
    settings_file = claude_dir / "settings.json"
    hook_file = hook_dir / "destructive-command-blocker.py"

    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, hook_file)
    make_executable(hook_file)

    settings = read_settings(settings_file)
    command = hook_command(hook_file)
    add_hook(settings, command)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed destructive command blocker at {hook_file}")
    print(f"Updated Claude Code settings at {settings_file}")
    return 0


def make_executable(path: Path) -> None:
    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def read_settings(settings_file: Path) -> dict[str, object]:
    if not settings_file.exists():
        return {}

    try:
        data = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {settings_file}: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Expected object JSON in {settings_file}")
    return data


def hook_command(hook_file: Path) -> str:
    if os.name == "nt":
        return f'"{sys.executable}" "{hook_file}"'
    return shlex.quote(str(hook_file))


def add_hook(settings: dict[str, object], command: str) -> None:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit("settings.hooks must be an object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit("settings.hooks.PreToolUse must be an array")

    for entry in pre_tool_use:
        if not isinstance(entry, dict):
            continue
        entry_hooks = entry.get("hooks")
        if not isinstance(entry_hooks, list):
            continue
        for hook in entry_hooks:
            if isinstance(hook, dict) and "destructive-command-blocker.py" in str(hook.get("command", "")):
                hook["type"] = "command"
                hook["command"] = command
                return

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": command}],
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
