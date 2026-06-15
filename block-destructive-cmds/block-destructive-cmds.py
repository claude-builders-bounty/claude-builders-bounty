#!/usr/bin/env python3
"""
pre-tool-use hook: Block destructive bash commands.

Claude Code pre-tool-use hook that intercepts dangerous bash
commands before they are executed. Supports configurable
allowlists, blocklists, and interactive confirmation.

Usage:
  # Direct execution (for testing):
  python3 block-destructive-cmds.py "rm -rf /"

  # As Claude Code pre-tool-use hook:
  # Place in .claude/hooks/pre-tool-use/ and make executable
"""

import os
import re
import sys
import json

# ── Configuration ──────────────────────────────────────────────────────

# These patterns are ALWAYS blocked without confirmation
HARD_BLOCK_PATTERNS = [
    # Disk destruction
    r"(^|\s)(dd|mkfs|fdisk|parted|mkswap)\s+",
    r"(^|\s)format\s+(com\s+)?[c-z]:",
    r">\s*/dev/(sda|sdb|sdc|sdd|nvme|mmcblk|xvd)",
    # rm -rf on root or home
    r"rm\s+(-[rf]+\s+)*/\s*($|#|;)",
    r"rm\s+(-[rf]+\s+)*~/?\s*($|#|;)",
    r"rm\s+(-[rf]+\s+)*/etc\b",
    r"rm\s+(-[rf]+\s+)*/boot\b",
    r"rm\s+(-[rf]+\s+)*/usr\b",
    r"rm\s+(-[rf]+\s+)*/var/lib\b",
    r"rm\s+(-[rf]+\s+)*/sys\b",
    r"rm\s+(-[rf]+\s+)*/proc\b",
    r"rm\s+-rf\s+--no-preserve-root\b",
    # Fork bomb
    r":\(\)\s*\{",
    r":\|\{\s*:\|\s*:",
    # chmod dangerous
    r"chmod\s+(-R\s+)?777\s+/",
    r"chmod\s+(-R\s+)?0+\s+/",
    # chown dangerous
    r"chown\s+(-R\s+)?[^:]+:[^:\.]+\s+/",
    # Wipe commands
    r"(^|\s)wipefs?\s+(-[af]+\s+)?/dev/",
    r"(^|\s)shred\s+(-[fnz]+\s+)?/dev/",
    r"(^|\s)blkdiscard\s+/dev/",
]

WARN_PATTERNS = [
    # Dangerous sudo patterns
    r"sudo\s+(rm|chmod|chown|dd|mkfs)\s",
    # Pipe to shell
    r"\b(curl|wget)\b.*\|\s*(bash|sh|zsh)\b",
    # Recursive operations in repo
    r"find\s+\.\s+-type\s+f\s+-exec\s+rm",
    r"git\s+push\s+(-f|--force)\b",
    r"npm\s+publish\s+--force\b",
    # Database dangerous
    r"DROP\s+(TABLE|DATABASE)\b",
    r"TRUNCATE\s+\w+\s*(CASCADE)?\s*;?\s*$",
    # Disk usage
    r"(^|\s)(pv|mkfs|mkswap|swapon|swapoff)\s",
]

# Commands that are ALWAYS allowed (override blocklist)
ALLOWLIST_PREFIXES = [
    "ls", "cat", "echo", "cd", "pwd", "git status",
    "git diff", "git log", "git branch", "git checkout ",
    "npm test", "npm run", "pnpm", "yarn",
    "python", "node", "deno", "bun",
    "cargo", "go", "rustc",
    "docker ps", "docker compose", "docker exec",
    "kubectl get", "kubectl describe", "kubectl logs",
]


def check_allowlist(cmd: str) -> bool:
    """Return True if command is in the allowlist."""
    cmd_stripped = cmd.strip()
    for prefix in ALLOWLIST_PREFIXES:
        if cmd_stripped.startswith(prefix):
            return True
    return False


def check_hard_block(cmd: str) -> tuple[bool, str]:
    """Check if command matches hard block patterns."""
    for pattern in HARD_BLOCK_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, f"Blocked by pattern: {pattern}"
    return False, ""


def check_warn(cmd: str) -> list[str]:
    """Return list of warning patterns matched."""
    matches = []
    for pattern in WARN_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            matches.append(pattern)
    return matches


def main():
    if len(sys.argv) < 2:
        # Claude Code pre-tool-use hook mode: read from stdin
        try:
            payload = json.load(sys.stdin)
            cmd = payload.get("command", "")
        except (json.JSONDecodeError, KeyError):
            print("Usage: block-destructive-cmds.py <command>", file=sys.stderr)
            sys.exit(1)
    else:
        cmd = " ".join(sys.argv[1:])

    if not cmd or check_allowlist(cmd):
        # Allow by default
        print(json.dumps({"decision": "allow", "command": cmd}))
        return

    blocked, reason = check_hard_block(cmd)
    if blocked:
        print(json.dumps({
            "decision": "block",
            "command": cmd,
            "reason": reason
        }))
        print(f"[block-destructive-cmds] BLOCKED: {cmd}", file=sys.stderr)
        print(f"  Reason: {reason}", file=sys.stderr)
        sys.exit(1)

    warnings = check_warn(cmd)
    if warnings:
        print(json.dumps({
            "decision": "warn",
            "command": cmd,
            "warnings": warnings
        }), file=sys.stderr)
        print(f"[block-destructive-cmds] WARNING: {cmd}", file=sys.stderr)
        for w in warnings:
            print(f"  - Matched: {w}", file=sys.stderr)

    print(json.dumps({"decision": "allow", "command": cmd}))


if __name__ == "__main__":
    main()
