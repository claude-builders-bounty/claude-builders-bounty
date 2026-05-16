#!/usr/bin/env python3
"""Install the destructive bash guard hook for Claude Code.

Usage:
  python3 install.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"
HOOK_SOURCE = Path(__file__).parent / "block_destructive_bash.py"
HOOK_DEST = HOOKS_DIR / "block_destructive_bash.py"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_NAME = "block-destructive-bash.py"


def main() -> int:
    # 1. Copy the hook script
    if not HOOK_SOURCE.exists():
        print(f"Error: {HOOK_SOURCE} not found. Run install.py from the same directory.", file=sys.stderr)
        return 1

    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOOK_SOURCE, HOOK_DEST)
    HOOK_DEST.chmod(0o755)
    print(f"✓ Hook script installed: {HOOK_DEST}")

    # 2. Register in settings.json
    settings = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text())
        except json.JSONDecodeError:
            print(f"Warning: {SETTINGS_PATH} is invalid JSON. Overwriting.", file=sys.stderr)
            settings = {}

    hooks = settings.get("hooks", [])
    # Check if already registered
    already_registered = any(
        isinstance(h, dict) and h.get("matcher", {}).get("command") == HOOK_NAME
        for h in hooks
    )

    if not already_registered:
        hooks.append({
            "type": "PreToolUse",
            "matcher": {"command": HOOK_NAME},
            "workingDirectory": str(HOOKS_DIR),
        })
        settings["hooks"] = hooks
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n")
        print(f"✓ Hook registered in {SETTINGS_PATH}")
    else:
        print(f"→ Hook already registered in settings.json (skipped)")

    print()
    print("✅ Installation complete! The hook will block destructive bash commands.")
    print("   Restart Claude Code for changes to take effect.")
    print()
    print("   To uninstall: python3 uninstall.py")
    print("   To disable temporarily: mv ~/.claude/hooks/block-destructive-bash.py{,.disabled}")
    print("   View blocked attempts: cat ~/.claude/hooks/blocked.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
