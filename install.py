#!/usr/bin/env python3
"""Install the dangerous Bash command guard into ~/.claude/hooks."""

from __future__ import annotations

import json
import shlex
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / ".claude" / "hooks" / "block_dangerous_bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOK_DIR = CLAUDE_DIR / "hooks"
DEST_HOOK = HOOK_DIR / "block_dangerous_bash.py"
SETTINGS = CLAUDE_DIR / "settings.json"


def _load_settings() -> dict:
    if not SETTINGS.exists():
        return {}
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = SETTINGS.with_suffix(".json.bak")
        shutil.copy2(SETTINGS, backup)
        return {}


def _install_hook(settings: dict) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"python3 {shlex.quote(str(DEST_HOOK))}"
    hook = {"type": "command", "command": command}

    for existing in pre_tool_use:
        if existing.get("matcher") != "Bash":
            continue
        existing_hooks = existing.setdefault("hooks", [])
        if not any(existing_hook.get("command") == command for existing_hook in existing_hooks):
            existing_hooks.append(hook)
        return settings

    pre_tool_use.append({"matcher": "Bash", "hooks": [hook]})
    return settings


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, DEST_HOOK)
    DEST_HOOK.chmod(0o755)

    settings = _install_hook(_load_settings())
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed {DEST_HOOK}")
    print(f"Updated {SETTINGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
