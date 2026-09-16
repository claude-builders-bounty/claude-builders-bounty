#!/usr/bin/env python3
"""
Installer for Claude Code Pre-Tool-Use Destructive Command Guard Hook.
Copies hook to ~/.claude/hooks/ and configures permissions in 1 step.
"""

import os
import shutil
import sys
from pathlib import Path

def install():
    home = Path.home()
    dest_dir = home / ".claude" / "hooks"
    dest_dir.mkdir(parents=True, exist_ok=True)

    src_py = Path(__file__).parent / "hooks" / "block_destructive.py"
    src_sh = Path(__file__).parent / "hooks" / "block_destructive.sh"

    dest_py = dest_dir / "block_destructive.py"
    dest_sh = dest_dir / "block_destructive.sh"

    shutil.copy2(src_py, dest_py)
    shutil.copy2(src_sh, dest_sh)

    if os.name != "nt":
        dest_py.chmod(0o755)
        dest_sh.chmod(0o755)

    print("✅ Claude Code pre-tool-use hook successfully installed!")
    print(f"📁 Location: {dest_dir}")
    print(f"📜 Log File: {dest_dir / 'blocked.log'}")

if __name__ == "__main__":
    install()
