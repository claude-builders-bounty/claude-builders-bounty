#!/usr/bin/env python3
"""Install the dangerous Bash command hook for Claude Code."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys


HOOK_NAME = "block-dangerous-bash.py"


def _load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup_path = settings_path.with_suffix(".json.bak")
        shutil.copy2(settings_path, backup_path)
        return {}

    return data if isinstance(data, dict) else {}


def _ensure_hook_config(settings: dict, hook_command: str) -> bool:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for matcher_group in pre_tool_use:
        if matcher_group.get("matcher") != "Bash":
            continue

        group_hooks = matcher_group.setdefault("hooks", [])
        if any(hook.get("command") == hook_command for hook in group_hooks):
            return False

        group_hooks.append({"type": "command", "command": hook_command})
        return True

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": hook_command}],
        }
    )
    return True


def main() -> int:
    source_hook = Path(__file__).resolve().with_name(HOOK_NAME)
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    destination_hook = hooks_dir / HOOK_NAME
    shutil.copy2(source_hook, destination_hook)

    settings = _load_settings(settings_path)
    hook_command = f'"{sys.executable}" "{destination_hook}"'
    changed = _ensure_hook_config(settings, hook_command)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {HOOK_NAME} to {hooks_dir}")
    if changed:
        print(f"Registered PreToolUse Bash hook in {settings_path}")
    else:
        print("PreToolUse Bash hook was already registered")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
