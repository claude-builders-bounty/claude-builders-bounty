#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install the hook into ~/.claude/settings.json with one command."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block_dangerous_bash.py"
HOME = Path.home()
HOOK_DIR = HOME / ".claude" / "hooks"
SETTINGS = HOME / ".claude" / "settings.json"
COMMAND = f'"{sys.executable}" "{HOOK_DIR / "block_dangerous_bash.py"}"'


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    target = HOOK_DIR / HOOK.name
    shutil.copy2(HOOK, target)
    target.chmod(0o755)

    settings = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"warning: could not parse {SETTINGS}: {exc}", file=sys.stderr)
            print("please merge the hook snippet manually; see README.md", file=sys.stderr)
            return 1

    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": COMMAND}]}
    if not any(h.get("matcher") == "Bash" and any(x.get("command") == COMMAND for x in h.get("hooks", [])) for h in pre):
        pre.append(entry)

    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"installed hook: {target}")
    print(f"updated settings: {SETTINGS}")
    print("restart Claude Code (or reload hooks) to activate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
