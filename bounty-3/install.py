#!/usr/bin/env python3
"""Install the destructive Bash guard into the current user's Claude Code config."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = ROOT / ".claude" / "hooks" / "destructive_bash_guard.py"


def main() -> int:
    if not SOURCE_HOOK.exists():
        print(f"Hook source not found: {SOURCE_HOOK}", file=sys.stderr)
        return 1

    claude_dir = Path.home() / ".claude"
    hook_dir = claude_dir / "hooks"
    destination = hook_dir / "destructive_bash_guard.py"
    settings_path = claude_dir / "settings.json"

    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, destination)
    destination.chmod(destination.stat().st_mode | stat.S_IXUSR)

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(
                f"Refusing to overwrite invalid JSON in {settings_path}: {exc}",
                file=sys.stderr,
            )
            return 1
    else:
        settings = {}

    pre_tool_use = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    command = str(destination)

    already_installed = any(
        entry.get("matcher") == "Bash"
        and any(hook.get("command") == command for hook in entry.get("hooks", []))
        for entry in pre_tool_use
    )
    if not already_installed:
        pre_tool_use.append({
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": command}],
        })

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook: {destination}")
    print(f"Updated settings: {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
