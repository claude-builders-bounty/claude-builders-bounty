#!/usr/bin/env python3
"""Install the destructive Bash command guard for Claude Code."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"


def main() -> int:
    source_hook = Path(__file__).with_name(HOOK_NAME)
    claude_dir = claude_config_dir()
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    target_hook = hooks_dir / HOOK_NAME

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_hook, target_hook)
    make_executable(target_hook)

    settings = load_settings(settings_path)
    add_pre_tool_use_hook(settings, target_hook)
    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Installed hook: {target_hook}")
    print(f"Updated settings: {settings_path}")
    return 0


def claude_config_dir() -> Path:
    configured_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured_dir) if configured_dir else Path.home() / ".claude"


def make_executable(path: Path) -> None:
    try:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse existing Claude settings: {path}: {exc}") from exc

    if not isinstance(settings, dict):
        raise SystemExit(f"Claude settings must be a JSON object: {path}")

    return settings


def add_pre_tool_use_hook(settings: dict[str, Any], hook_path: Path) -> None:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit("Claude settings field 'hooks' must be a JSON object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit("Claude settings field 'hooks.PreToolUse' must be a JSON array")

    bash_matcher = find_or_create_bash_matcher(pre_tool_use)
    matcher_hooks = bash_matcher.setdefault("hooks", [])
    if not isinstance(matcher_hooks, list):
        raise SystemExit("Claude Bash matcher field 'hooks' must be a JSON array")

    command = f'"{sys.executable}" "{hook_path}"'
    if any(
        isinstance(hook, dict)
        and hook.get("type") == "command"
        and HOOK_NAME in str(hook.get("command", ""))
        for hook in matcher_hooks
    ):
        return

    matcher_hooks.append({"type": "command", "command": command})


def find_or_create_bash_matcher(pre_tool_use: list[Any]) -> dict[str, Any]:
    for matcher in pre_tool_use:
        if isinstance(matcher, dict) and matcher.get("matcher") == "Bash":
            return matcher

    matcher = {"matcher": "Bash", "hooks": []}
    pre_tool_use.append(matcher)
    return matcher


if __name__ == "__main__":
    raise SystemExit(main())
