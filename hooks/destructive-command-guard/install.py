#!/usr/bin/env python3
"""Install the destructive command guard hook into Claude Code settings."""

from __future__ import annotations

import json
import shlex
import shutil
from pathlib import Path
from typing import Any


def main() -> int:
    home = Path.home()
    hooks_dir = home / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    source = Path(__file__).with_name("destructive_command_guard.py")
    target = hooks_dir / "destructive_command_guard.py"
    shutil.copy2(source, target)

    settings_path = home / ".claude" / "settings.json"
    settings = _read_settings(settings_path)
    command = f"python3 {shlex.quote(str(target))}"
    _upsert_hook(settings, command)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook script: {target}")
    print(f"Updated Claude Code settings: {settings_path}")
    return 0


def _read_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Cannot parse existing settings file {settings_path}: {error}") from error


def _upsert_hook(settings: dict[str, Any], command: str) -> None:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for matcher_config in pre_tool_use:
        if matcher_config.get("matcher") != "Bash":
            continue
        command_hooks = matcher_config.setdefault("hooks", [])
        if not any(hook.get("type") == "command" and hook.get("command") == command for hook in command_hooks):
            command_hooks.append({"type": "command", "command": command})
        return

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": command}],
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
