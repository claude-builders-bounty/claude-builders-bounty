#!/usr/bin/env python3
"""Install the destructive Bash command blocker into Claude Code settings."""

from __future__ import annotations

import json
import os
import shutil
import stat
from pathlib import Path


HOOK_NAME = "block_destructive_bash.py"


def command_for(path: Path) -> str:
    return f"python3 {path}"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    source_hook = repo_root / "hooks" / HOOK_NAME
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    target_hook = hooks_dir / HOOK_NAME

    hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_hook, target_hook)
    target_hook.chmod(target_hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            raise ValueError(f"{settings_path} must contain a JSON object")
    else:
        settings = {}

    pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    hook_command = command_for(target_hook)
    entry = {"type": "command", "command": hook_command}
    matcher_block = next(
        (item for item in pre_tool_use if isinstance(item, dict) and item.get("matcher") == "Bash"),
        None,
    )
    if matcher_block is None:
        pre_tool_use.append({"matcher": "Bash", "hooks": [entry]})
    else:
        hooks = matcher_block.setdefault("hooks", [])
        if entry not in hooks:
            hooks.append(entry)

    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.chmod(settings_path, 0o600)

    print(f"Installed {target_hook}")
    print(f"Updated {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
