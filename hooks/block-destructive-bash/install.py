#!/usr/bin/env python3
"""Install the destructive Bash guard into the user's Claude Code hooks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path


HOOK_NAME = "block_destructive_bash.py"


def _quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def _load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _add_hook(settings: dict, command: str) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for matcher in pre_tool_use:
        if matcher.get("matcher") != "Bash":
            continue
        matcher_hooks = matcher.setdefault("hooks", [])
        if any(hook.get("type") == "command" and hook.get("command") == command for hook in matcher_hooks):
            return False
        matcher_hooks.append({"type": "command", "command": command})
        return True

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": command}],
        }
    )
    return True


def install(claude_home: Path, python_command: str) -> tuple[Path, Path, bool]:
    source = Path(__file__).with_name(HOOK_NAME)
    hooks_dir = claude_home / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target = hooks_dir / HOOK_NAME
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = claude_home / "settings.json"
    settings = _load_settings(settings_path)
    command = f"{_quote(python_command)} {_quote(str(target))}"
    changed = _add_hook(settings, command)

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    return target, settings_path, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--claude-home",
        default=str(Path.home() / ".claude"),
        help="Claude configuration directory. Defaults to ~/.claude.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python command Claude Code should use when running the hook.",
    )
    args = parser.parse_args()

    target, settings_path, changed = install(Path(args.claude_home).expanduser(), args.python)
    action = "registered" if changed else "already registered"
    print(f"Installed hook: {target}")
    print(f"Updated settings: {settings_path} ({action})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
