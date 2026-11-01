#!/usr/bin/env python3
"""
Installer for Claude Code Pre-Tool-Use Destructive Command Blocker.
Installs hook into ~/.claude/hooks/pre-tool-use.
"""

import os
import sys
import shutil
from pathlib import Path

def install():
    home = Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or Path.home())
    hooks_dir = home / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    src_file = Path(__file__).resolve().parent / "hooks" / "block_destructive.py"
    dest_file = hooks_dir / "pre-tool-use"

    shutil.copy2(src_file, dest_file)
    try:
        dest_file.chmod(0o755)
    except Exception:
        pass

    print(f"✅ Successfully installed hook to {dest_file}")
    print("🛡️ Claude Code is now protected against destructive bash commands.")

if __name__ == "__main__":
    install()
