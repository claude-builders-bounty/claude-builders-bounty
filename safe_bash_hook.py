#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block destructive bash commands.

For the $100 bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

Install in 2 commands (see README).
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Pattern

# Dangerous patterns (case-insensitive where appropriate)
DANGEROUS_PATTERNS: List[Pattern] = [
    re.compile(r'rms+(-[rfRF]*s*)*s*/', re.I),                    # rm -rf /
    re.compile(r'rms+(-[rfRF]*s*)*s*~', re.I),                    # rm -rf ~
    re.compile(r'gits+pushs+--force', re.I),
    re.compile(r'DROPs+TABLE', re.I),
    re.compile(r'TRUNCATEs+TABLE?', re.I),
    re.compile(r'DELETEs+FROM(?!s+w+s+WHERE)', re.I),          # DELETE FROM without WHERE
    re.compile(r'sudos+rms+-rfs+/', re.I),
    re.compile(r'chmods+-Rs+777s+/', re.I),
    re.compile(r':(){ :|:& };:', re.I),                              # fork bomb
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def is_destructive(command: str) -> bool:
    """Return True if command matches any dangerous pattern."""
    cmd = command.strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(cmd):
            return True
    return False

def log_blocked(command: str, project_path: str):
    """Append to log file."""
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path or os.getcwd(),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "
")

def main():
    # Claude Code typically passes the command as first argument for bash tool
    # or via env var / stdin. We support common patterns.
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        # Fallback: read from stdin or env
        command = os.environ.get("CLAUDE_COMMAND", "")
        if not command:
            try:
                command = sys.stdin.read().strip()
            except:
                command = ""

    if not command:
        # Nothing to check, allow
        sys.exit(0)

    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    if is_destructive(command):
        log_blocked(command, project_path)
        msg = (
            f"🛑 BLOCKED by safe-bash-hook
"
            f"Command: {command}
"
            f"Reason: Matches dangerous pattern (rm -rf, force push, destructive SQL, etc.)
"
            f"Logged to: {LOG_PATH}"
        )
        print(msg, file=sys.stderr)
        # Exit non-zero to block the tool call
        sys.exit(1)

    # Safe — allow the command
    sys.exit(0)

if __name__ == "__main__":
    main()
