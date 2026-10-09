#!/usr/bin/env python3
"""Install the destructive-command guard into ~/.claude without clobbering settings."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "hooks" / "pre-tool-use.py"


def main() -> int:
    home = Path(os.environ.get("HOME") or Path.home())
    claude_dir = home / ".claude"
    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    dest_hook = hooks_dir / "pre-tool-use.py"
    shutil.copyfile(SOURCE_HOOK, dest_hook)
    dest_hook.chmod(dest_hook.stat().st_mode | 0o111)

    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        raw = settings_path.read_text(encoding="utf-8")
        settings = json.loads(raw) if raw.strip() else {}
        if not isinstance(settings, dict):
            raise RuntimeError("~/.claude/settings.json must contain a JSON object")
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise RuntimeError("settings.hooks must be a JSON object")
    pre_tool = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool, list):
        raise RuntimeError("settings.hooks.PreToolUse must be a JSON array")

    command = f"python3 {shlex.quote(str(dest_hook))}"
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    already_present = False
    for group in pre_tool:
        if not isinstance(group, dict) or group.get("matcher") != "Bash":
            continue
        handlers = group.get("hooks")
        if not isinstance(handlers, list):
            continue
        if any(isinstance(item, dict) and item.get("command") == command for item in handlers):
            already_present = True
            break
    if not already_present:
        pre_tool.append(entry)

    tmp_path = settings_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp_path, settings_path)

    print(f"Installed hook: {dest_hook}")
    print(f"Updated settings: {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
