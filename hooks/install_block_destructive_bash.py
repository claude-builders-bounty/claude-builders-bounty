#!/usr/bin/env python3
"""Install the destructive Bash command blocker into ~/.claude/hooks."""

from __future__ import annotations

import json
import os
import shlex
import shutil
from pathlib import Path


HOOK_NAME = "block_destructive_bash.py"


def main() -> int:
    source = Path(__file__).resolve().with_name(HOOK_NAME)
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    target = hooks_dir / HOOK_NAME

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    try:
        target.chmod(target.stat().st_mode | 0o111)
    except OSError:
        pass

    settings: dict[str, object]
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            raise ValueError(f"{settings_path} must contain a JSON object")
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be a JSON object")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise ValueError("settings.hooks.PreToolUse must be a JSON array")

    command = f"python3 {shlex.quote(str(target))}"
    matcher = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    has_command = any(
        isinstance(item, dict)
        and any(
            isinstance(hook, dict) and hook.get("command") == command
            for hook in item.get("hooks", [])
        )
        for item in pre_tool_use
    )
    if not has_command:
        pre_tool_use.append(matcher)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed {target}")
    print(f"Updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
