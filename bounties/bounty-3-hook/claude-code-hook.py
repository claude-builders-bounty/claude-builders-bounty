#!/usr/bin/env python3
"""
claude-code-hook.py — Pre-tool-use hook that blocks destructive bash commands.

Claude Code calls this hook before every tool use. It receives JSON on stdin
with the tool call details. If the command matches destructive patterns, it
prints a warning and exits non-zero to block execution.

Bypass: set env CLAUDE_ALLOW_DESTRUCTIVE=1 to skip all checks.
"""

import json
import os
import re
import sys
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "blocked_commands.log"

# ── Destructive patterns ────────────────────────────────────────

DESTRUCTIVE_PATTERNS = [
    # rm -rf everything
    (r'\brm\s+(-rf?|--recursive)\s+(/\s*|/\*\s*|\$\{?\w*[Rr][Oo][Oo][Tt]?\}?\s*\*?)',
     "DANGER: Recursive delete of root filesystem or wildcard root"),
    (r'\brm\s+(-rf?|--recursive)\s+(/\w+)?\s*/\*\s*',
     "DANGER: Recursive delete of system directory"),

    # Fork bomb
    (r':\(\)\s*\{[\s\S]*:\s*\|\s*:\s*&[\s\S]*\};?\s*:',
     "DANGER: Fork bomb — will crash the system"),

    # dd destructive writes
    (r'\bdd\s+.*if=(/dev/zero|/dev/random)',
     "DANGER: dd overwriting system memory or disk"),
    (r'\bdd\s+.*of=\s*/(dev/sd[a-z]|dev/nvme|dev/mmc)',
     "DANGER: dd writing directly to a block device"),

    # chmod -R 777 /
    (r'\bchmod\s+-R?\s*777\s+/[\s*]?',
     "DANGER: Making entire filesystem world-writable"),

    # mv / to /dev/null
    (r'\bmv\s+/\s+\S*null',
     "DANGER: Moving root filesystem to /dev/null"),

    # curl/wget pipe to bash/sh
    (r'(curl|wget)\s+.*\|\s*(bash|sh|zsh|dash)',
     "BLOCKED: Piping remote script directly to shell (supply-chain risk). "
     "Use --bypass if you've reviewed the source."),

    # Disk wipe
    (r'\bmkfs\.\w+\s+/dev/',
     "DANGER: Formatting a block device"),
    (r'\bmkswap\s+/dev/',
     "DANGER: Setting up swap on a block device (data loss)"),

    # chown -R /
    (r'\bchown\s+-R\s+\w+:\w+\s+/[\s*]?',
     "DANGER: Recursive ownership change on root filesystem"),

    # Dangerous git operations
    (r'\bgit\s+push\s+--force\s+',
     "WARNING: Force push will overwrite remote history"),
    (r'\bgit\s+push\s+origin\s+\+?\w+:\w+',
     "WARNING: Force-push with +refspec"),

    # Mass delete in critical dirs
    (r'\bfind\s+/\s+-delete\b',
     "DANGER: Recursive deletion from root via find"),
    (r'\bfind\s+/etc\s+.*-delete\b',
     "DANGER: Deleting system configuration files"),
    (r'\bfind\s+/usr\s+.*-delete\b',
     "DANGER: Deleting system binaries/libraries"),
]

# Safe patterns — commands that look destructive but are OK
SAFE_PATTERNS = [
    r'\brm\s+(-rf?|--recursive)\s+(\S+)?(node_modules|\.next|dist|build|\.git|\.cache|\.venv)\b',
    r'\brm\s+\S+\.(txt|md|json|yaml|yml|toml|env|log|js|ts|tsx|jsx|css|scss|py|rb|go|rs|c|cpp|h|hpp)',
    r'\brm\s+-rf?\s+\.git/index\.lock\b',
    r'\bfind\s+\S+\s+.*-delete\b',
]


def should_block(command: str) -> tuple[bool, str]:
    """Check if a command should be blocked. Returns (block, reason)."""
    # If bypass env is set, allow everything
    if os.environ.get("CLAUDE_ALLOW_DESTRUCTIVE", "") == "1":
        return False, ""

    # First check if it's a known safe pattern
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, ""

    # Then check destructive patterns
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason

    return False, ""


def log_blocked(command: str, reason: str):
    """Log blocked command to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = __import__('datetime').datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  Command: {command}\n")
        f.write(f"  Bypass:  CLAUDE_ALLOW_DESTRUCTIVE=1\n")
        f.write("-" * 60 + "\n")


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Not a hook invocation — maybe being tested manually
        print("⛔ claude-code-hook: no JSON payload received (not running as Claude Code hook)")
        sys.exit(0)

    # Extract the tool call
    tool = payload.get("tool", "")
    args = payload.get("args", {})
    command = ""

    if tool in ("Bash", "bash", "Terminal", "terminal"):
        command = args.get("command", "")
    elif tool in ("Write", "write", "Edit", "edit"):
        content = args.get("content", "")
        path = args.get("path", "")
        # Check if writing to critical system paths
        critical_paths = [
            r'^/etc/',
            r'^/usr/',
            r'^/bin/',
            r'^/sbin/',
            r'^/boot/',
            r'^/dev/',
        ]
        for p in critical_paths:
            if re.match(p, path):
                print(f"⛔ BLOCKED: Writing to system path '{path}'")
                log_blocked(f"Write({path})", f"Writing to system path '{path}'")
                sys.exit(1)
        return

    if not command:
        return  # Not a bash command, allow

    block, reason = should_block(command)
    if block:
        print(f"\n{'=' * 60}")
        print(f"⛔  BLOCKED — Destructive Command")
        print(f"{'=' * 60}")
        print(f"")
        print(f"  Reason: {reason}")
        print(f"")
        print(f"  Command: {command}")
        print(f"")
        print(f"  To bypass, run with: CLAUDE_ALLOW_DESTRUCTIVE=1")
        print(f"{'=' * 60}\n")

        log_blocked(command, reason)
        sys.exit(1)

    # Command is safe
    sys.exit(0)


if __name__ == "__main__":
    main()
