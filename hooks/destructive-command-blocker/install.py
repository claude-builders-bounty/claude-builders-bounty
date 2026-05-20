#!/usr/bin/env python3
"""Install the destructive Bash command blocker into Claude Code settings."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"


def _load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Refusing to edit invalid JSON in {path}: {error}") from error


def _same_hook(existing: dict[str, Any], python_path: str, hook_path: str) -> bool:
    return (
        existing.get("type") == "command"
        and existing.get("command") == python_path
        and existing.get("args") == [hook_path]
    )


def _merge_hook(settings: dict[str, Any], python_path: str, hook_path: str) -> dict[str, Any]:
    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    for group in pre_tool:
        if group.get("matcher") != "Bash":
            continue
        group_hooks = group.setdefault("hooks", [])
        if any(_same_hook(hook, python_path, hook_path) for hook in group_hooks):
            return settings
        group_hooks.append({"type": "command", "command": python_path, "args": [hook_path]})
        return settings

    pre_tool.append(
        {
            "matcher": "Bash",
            "hooks": [
                {"type": "command", "command": python_path, "args": [hook_path]},
            ],
        }
    )
    return settings


def main() -> int:
    source_dir = Path(__file__).resolve().parent
    source_hook = source_dir / HOOK_NAME

    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    target_hook = hooks_dir / HOOK_NAME
    settings_path = claude_dir / "settings.json"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_hook, target_hook)

    if os.name != "nt":
        target_hook.chmod(target_hook.stat().st_mode | stat.S_IXUSR)

    settings = _load_settings(settings_path)
    _merge_hook(settings, sys.executable, str(target_hook))

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook: {target_hook}")
    print(f"Updated settings: {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
