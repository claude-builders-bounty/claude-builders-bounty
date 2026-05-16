#!/usr/bin/env python3
"""Install the destructive Bash command guard into ~/.claude/hooks."""

from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path


def _load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")


def main() -> int:
    source = Path(__file__).with_name("block_destructive_bash.py").resolve()
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    target = hooks_dir / "block_destructive_bash.py"
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = claude_dir / "settings.json"
    settings = _load_settings(settings_path)
    pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    command = str(target)

    already_installed = any(
        hook.get("command") == command
        for group in pre_tool_use
        for hook in group.get("hooks", [])
    )
    if not already_installed:
        pre_tool_use.append(
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": command,
                    }
                ],
            }
        )

    _save_settings(settings_path, settings)
    print(f"Installed {target}")
    print(f"Updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
