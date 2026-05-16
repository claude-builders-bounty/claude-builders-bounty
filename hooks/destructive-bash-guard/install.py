#!/usr/bin/env python3
"""Install the destructive Bash guard into a Claude Code settings file."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_bash_guard.py"


def default_settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def hook_entry() -> dict[str, Any]:
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": HOOK_COMMAND,
            }
        ],
    }


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        loaded = json.load(settings_file)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def has_guard_entry(pre_tool_use: list[Any]) -> bool:
    for item in pre_tool_use:
        if not isinstance(item, dict):
            continue
        if item.get("matcher") != "Bash":
            continue
        hooks = item.get("hooks")
        if not isinstance(hooks, list):
            continue
        for hook in hooks:
            if isinstance(hook, dict) and hook.get("command") == HOOK_COMMAND:
                return True
    return False


def merge_settings(settings: dict[str, Any]) -> dict[str, Any]:
    merged = dict(settings)
    hooks = merged.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        merged["hooks"] = hooks

    pre_tool_use = hooks.get("PreToolUse")
    if not isinstance(pre_tool_use, list):
        pre_tool_use = []
        hooks["PreToolUse"] = pre_tool_use

    if not has_guard_entry(pre_tool_use):
        pre_tool_use.append(hook_entry())

    return merged


def install(settings_path: Path | None = None, home: Path | None = None) -> Path:
    source = Path(__file__).with_name("destructive_bash_guard.py")
    home = home or Path.home()
    target_dir = home / ".claude" / "hooks"
    target = target_dir / "destructive_bash_guard.py"
    settings_path = settings_path or default_settings_path()

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o755)

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = merge_settings(load_settings(settings_path))
    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    return settings_path


def main() -> int:
    settings_arg = sys.argv[1] if len(sys.argv) > 1 else None
    settings_path = Path(settings_arg).expanduser() if settings_arg else None
    installed_settings = install(settings_path)
    print(f"Installed destructive Bash guard in {installed_settings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
