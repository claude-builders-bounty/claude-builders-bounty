#!/usr/bin/env python3
"""Install the destructive command blocker into Claude Code user settings."""

from __future__ import annotations

import json
import shutil
import stat
import sys
from pathlib import Path


HOOK_FILENAME = "block_destructive_commands.py"


def main() -> int:
    source = Path(__file__).with_name(HOOK_FILENAME)
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    target = hooks_dir / HOOK_FILENAME

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR)

    settings = read_settings(settings_path)
    add_hook(settings, target)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed hook script: {target}")
    print(f"Updated Claude settings: {settings_path}")
    return 0


def read_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}

    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse {settings_path}: {exc}") from exc


def add_hook(settings: dict, hook_path: Path) -> None:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    handler = {
        "type": "command",
        "command": sys.executable,
        "args": [str(hook_path)],
        "timeout": 10,
    }

    for group in pre_tool_use:
        if group.get("matcher") != "Bash":
            continue
        group_hooks = group.setdefault("hooks", [])
        if not contains_handler(group_hooks, handler):
            group_hooks.append(handler)
        return

    pre_tool_use.append({"matcher": "Bash", "hooks": [handler]})


def contains_handler(group_hooks: list[dict], handler: dict) -> bool:
    for existing in group_hooks:
        if (
            existing.get("type") == handler["type"]
            and existing.get("command") == handler["command"]
            and existing.get("args") == handler["args"]
        ):
            return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
