#!/usr/bin/env python3
"""Install the destructive Bash guard into the user's Claude Code settings."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any


def settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def hook_target_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "block_destructive_bash.py"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def install_hook_script(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if os.name != "nt":
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def hook_handler(target: Path) -> dict[str, Any]:
    return {
        "type": "command",
        "command": sys.executable,
        "args": [str(target)],
    }


def ensure_settings_entry(settings: dict[str, Any], target: Path) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    handler = hook_handler(target)

    for group in pre_tool_use:
        if group.get("matcher") != "Bash":
            continue
        handlers = group.setdefault("hooks", [])
        for existing in handlers:
            if existing.get("args") == handler["args"]:
                return False
        handlers.append(handler)
        return True

    pre_tool_use.append({"matcher": "Bash", "hooks": [handler]})
    return True


def main() -> int:
    source = Path(__file__).with_name("block_destructive_bash.py")
    target = hook_target_path()
    install_hook_script(source, target)

    settings_file = settings_path()
    settings = load_settings(settings_file)
    changed = ensure_settings_entry(settings, target)
    save_settings(settings_file, settings)

    print(f"Installed hook: {target}")
    print(f"Updated settings: {settings_file}" if changed else f"Settings already contained hook: {settings_file}")
    print(f"Blocked attempts will be logged to: {Path.home() / '.claude' / 'hooks' / 'blocked.log'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
