#!/usr/bin/env python3
"""
Cross-Platform 1-Command Installer for Claude Code Destructive Bash Command Interceptor Hook.

Usage:
    python3 install.py
"""

import sys
import os
import json
import shutil
from pathlib import Path


def install():
    print("Installing Claude Code Destructive Bash Command Interceptor Hook...")

    home = Path.home()
    claude_dir = home / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_file = claude_dir / "settings.json"

    # 1. Create directory ~/.claude/hooks
    hooks_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [+] Ensured directory exists: {hooks_dir}")

    # 2. Locate source hook file
    repo_root = Path(__file__).resolve().parent
    source_hook = repo_root / "hooks" / "block-destructive" / "block_destructive.py"
    if not source_hook.exists():
        print(f"  [-] Error: Source hook file not found at {source_hook}")
        sys.exit(1)

    dest_hook = hooks_dir / "block_destructive.py"
    shutil.copy2(source_hook, dest_hook)
    try:
        dest_hook.chmod(0o755)
    except Exception:
        pass
    print(f"  [+] Installed hook script to: {dest_hook}")

    # 3. Configure ~/.claude/settings.json
    hook_command = f"python3 {dest_hook}"
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}

    hooks_config = settings.setdefault("hooks", {})
    pre_tool_use = hooks_config.setdefault("PreToolUse", [])

    # Check if already installed
    already_installed = False
    for entry in pre_tool_use:
        matcher = entry.get("matcher", "")
        if matcher.lower() == "bash":
            for h in entry.get("hooks", []):
                if "block_destructive.py" in h.get("command", ""):
                    already_installed = True
                    break

    if not already_installed:
        pre_tool_use.append({
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": hook_command
                }
            ]
        })
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        print(f"  [+] Registered PreToolUse hook in: {settings_file}")
    else:
        print(f"  [+] Hook already registered in: {settings_file}")

    print("\n[SUCCESS] Installation complete! Destructive commands are now guarded by Claude Code.")


if __name__ == "__main__":
    install()
