#!/usr/bin/env python3
"""Install the destructive-command hook into ~/.claude."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


HOOK_EVENT = "PreToolUse"
HOOK_MATCHER = "Bash"


def command_for(script_path: Path) -> str:
    return f'"{sys.executable}" "{script_path}"'


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}
    return json.loads(settings_path.read_text(encoding="utf-8"))


def claude_config_dir() -> Path:
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude"


def install() -> None:
    source = Path(__file__).with_name("block_destructive.py")
    config_dir = claude_config_dir()
    hooks_dir = config_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target = hooks_dir / "block_destructive.py"
    shutil.copy2(source, target)

    settings_path = config_dir / "settings.json"
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault(HOOK_EVENT, [])
    hook_entry = {
        "matcher": HOOK_MATCHER,
        "hooks": [{"type": "command", "command": command_for(target)}],
    }

    if hook_entry not in pre_tool_use:
        pre_tool_use.append(hook_entry)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {target}")
    print(f"Updated settings at {settings_path}")


if __name__ == "__main__":
    install()
