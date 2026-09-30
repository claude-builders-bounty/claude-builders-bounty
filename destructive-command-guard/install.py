#!/usr/bin/env python3
"""
Installer for Claude Code PreToolUse Destructive Command Guard
Copies hook script to ~/.claude/hooks/ and ensures executable permissions.
"""

import os
import sys
import shutil

def install():
    home_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    hooks_dir = os.path.join(home_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre_tool_use_guard.py")
    dest = os.path.join(hooks_dir, "pre_tool_use_guard.py")

    shutil.copy2(src, dest)
    try:
        os.chmod(dest, 0o755)
    except Exception:
        pass

    print(f"✅ Successfully installed PreToolUse guard to: {dest}")
    print(f"📝 Audit log will be saved to: {os.path.join(hooks_dir, 'blocked.log')}")

if __name__ == "__main__":
    install()
