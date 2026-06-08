#!/usr/bin/env python3
"""Install the destructive Bash guard hook into the user's Claude settings."""

from __future__ import annotations

import json
import shutil
import stat
import sys
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"


def quote_arg(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def hook_command(python_executable: str, hook_path: Path) -> str:
    return f"{quote_arg(python_executable)} {quote_arg(str(hook_path))}"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def save_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")


def ensure_hook(settings: dict[str, Any], command: str) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    hook_entry = {
        "type": "command",
        "command": command,
    }

    for matcher_group in pre_tool_use:
        if matcher_group.get("matcher") != "Bash":
            continue
        group_hooks = matcher_group.setdefault("hooks", [])
        if any(existing.get("command") == command for existing in group_hooks):
            return False
        group_hooks.append(hook_entry)
        return True

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [hook_entry],
        }
    )
    return True


def install() -> tuple[Path, Path, bool]:
    source = Path(__file__).with_name(HOOK_NAME)
    hook_dir = Path.home() / ".claude" / "hooks"
    target = hook_dir / HOOK_NAME
    settings_path = Path.home() / ".claude" / "settings.json"

    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR)

    settings = load_settings(settings_path)
    changed = ensure_hook(settings, hook_command(sys.executable, target))
    save_settings(settings_path, settings)
    return target, settings_path, changed


def main() -> int:
    target, settings_path, changed = install()
    state = "updated" if changed else "already configured"
    print(f"Installed hook: {target}")
    print(f"Claude settings {state}: {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
