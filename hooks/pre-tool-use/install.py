#!/usr/bin/env python3
"""install.py — One-command install for the Claude Code blocker hook."""

import os
import shutil
import sys

HOOK_SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre-tool-use.py")
HOOK_DIR = os.path.expanduser("~/.claude/hooks")
HOOK_DEST = os.path.join(HOOK_DIR, "pre-tool-use")

os.makedirs(HOOK_DIR, exist_ok=True)
shutil.copy2(HOOK_SOURCE, HOOK_DEST)
os.chmod(HOOK_DEST, 0o755)

print(f"Hook installed: {HOOK_DEST}")
print(f"Blocked commands logged to: {HOOK_DIR}/blocked.log")
print()
print("To test in Claude Code, run: rm -rf /tmp/test")
print("The hook will block it.")
print()
print("To uninstall:")
print(f"  rm {HOOK_DEST}")
