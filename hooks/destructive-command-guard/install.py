#!/usr/bin/env python3
"""Install the destructive command guard into the current user's Claude settings."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path
from typing import Any


HOOK_NAME = "pre-tool-use-block-destructive.py"
COMMAND = f"python3 ~/.claude/hooks/{HOOK_NAME}"


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        return {}
    return data if isinstance(data, dict) else {}


def ensure_hook(settings: dict[str, Any]) -> None:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": COMMAND,
            }
        ],
    }
    for existing in pre_tool_use:
        if not isinstance(existing, dict):
            continue
        for hook in existing.get("hooks") or []:
            if isinstance(hook, dict) and hook.get("command") == COMMAND:
                return
    pre_tool_use.append(entry)


def main() -> int:
    source = Path(__file__).resolve().with_name(HOOK_NAME)
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target = hooks_dir / HOOK_NAME
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = claude_dir / "settings.json"
    settings = load_settings(settings_path)
    ensure_hook(settings)
    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Installed {target}")
    print(f"Updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
