#!/usr/bin/env python3
"""
safe-shell.py — PreToolUse hook for Claude Code that blocks destructive bash
commands before they run.

Register in .claude/settings.json:
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 /abs/path/safe-shell.py" } ] }
    ]
  }
}

Claude Code calls this with a JSON event on stdin. Exit 0 = allow.
Exit 2 with a JSON decision on stderr = BLOCK the tool call.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Patterns that, if matched, are BLOCKED outright.
BLOCK_PATTERNS = [
    (r"\brm\s+-rf?\s+/|rm\s+-rf?\s+/*\s*$", "Recursively deleting from filesystem root"),
    (r"\brm\s+-rf?\s+~|rm\s+-rf?\s+\$HOME", "Recursively deleting your home directory"),
    (r"\bgit\s+reset\s+--hard", "Hard reset — discards all uncommitted changes"),
    (r"\bgit\s+clean\s+-[a-z]*f[a-z]*d", "git clean -fd — deletes untracked files/directories"),
    (r"\bmkfs\.", "Formatting a filesystem (destroys all data on the device)"),
    (r"\bdd\s+if=.*of=/dev/", "Raw block write to a device with dd"),
    (r":\(\)\s*\{\s*:\|:&\s*\}", "Fork bomb"),
    (r"\bchmod\s+-R\s+777\s+/", "World-writable permissions on filesystem root"),
    (r"\bchown\s+-R\s+.*\s+/", "Recursive chown on filesystem root"),
    (r">\s*/dev/sd[a-z]", "Overwriting a raw disk device"),
    (r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b", "System power command"),
    (r"\bcurl\s+.*\|\s*(sudo\s+)?(ba)?sh\b", "Pipe-downloaded script straight into a shell"),
    (r"\bwget\s+.*\|\s*(sudo\s+)?(ba)?sh\b", "Pipe-downloaded script straight into a shell"),
    (r"\bmv\s+.*\s+/\s*$", "Moving files to filesystem root"),
    (r"\btruncate\s+-s\s+0\s+/", "Zeroing a file at filesystem root"),
]

COMPILED = [(re.compile(p, re.IGNORECASE), why) for p, why in BLOCK_PATTERNS]


def decision_block(reason: str) -> None:
    sys.stderr.write(json.dumps({"decision": "block", "reason": reason}) + "\n")
    sys.exit(2)


def main() -> None:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        sys.exit(0)  # can't parse -> allow (fail open, don't break the agent)

    if event.get("tool_name") not in ("Bash", "bash"):
        sys.exit(0)

    command = (event.get("tool_input", {}) or {}).get("command", "")
    if not command:
        sys.exit(0)

    for pattern, why in COMPILED:
        if pattern.search(command):
            decision_block(f"🛡️ safe-shell blocked a destructive command: {why}.\nCommand: `{command}`")
    sys.exit(0)


if __name__ == "__main__":
    main()
