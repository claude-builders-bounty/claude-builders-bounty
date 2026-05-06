#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands
v2.0 — Professional Python Implementation

Installation:
  mkdir -p ~/.claude/hooks
  ln -sf $PWD/pre-tool-use.py ~/.claude/hooks/pre-tool-use
  chmod +x ~/.claude/hooks/pre-tool-use

Claude Code calls pre-tool-use hooks with JSON payload on stdin:
  {"command": "rm -rf /", ...}
Exit 0 = allow, Exit non-zero = block with message.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import final

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
DETAILED_LOG = True  # Set to False for minimal logging

# ─────────────────────────────────────────────
#  Block Patterns: (name, regex, reason)
#  Each pattern is a compiled regex with clear
#  human-readable explanation for the block.
# ─────────────────────────────────────────────
BLOCK_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [

    # ── Filesystem Destruction ──
    ("rm -rf /", re.compile(
        r'(?:^|[;&|`$()\s\n])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\s+/',
        re.IGNORECASE
    ), "⚠️ Recursive force-delete on root (rm -rf /) — this destroys the entire system"),

    ("rm -rf /*", re.compile(
        r'(?:^|[;&|`$()\s\n])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\s+/\*',
        re.IGNORECASE
    ), "⚠️ Recursive force-delete on /* — this wipes all files"),

    ("rm -rf dangerous", re.compile(
        r'(?:^|[;&|`$()\s\n])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\s+(?:/[/\w-]+)?\s*$',
        re.IGNORECASE
    ), "⚠️ Recursive force-delete without safety check"),

    ("dd to disk", re.compile(
        r'\bdd\s+.*\b(?:of|if)\s*=\s*/dev/(?:sd|hd|nvme|vd|mmcblk)',
        re.IGNORECASE
    ), "⚠️ Direct disk write with dd — can destroy partitions and data"),

    ("mkfs / format", re.compile(
        r'\b(?:mkfs\.\w+|mkfs|format)\s+/dev/',
        re.IGNORECASE
    ), "⚠️ Filesystem creation command — will destroy data on the target device"),

    # ── Database Destruction ──
    ("DROP TABLE", re.compile(
        r'\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b',
        re.IGNORECASE
    ), "⚠️ Database object deletion — irreversible data loss"),

    ("TRUNCATE", re.compile(
        r'\bTRUNCATE\s+(?:TABLE\s+)?\w+',
        re.IGNORECASE
    ), "⚠️ Table data truncation — all rows will be permanently deleted"),

    ("DELETE without WHERE", re.compile(
        r'\bDELETE\s+FROM\s+\w+(?:\s+(?:FROM|USING)\s+\w+)*\s*;(?!\s*\n\s*WHERE)',
        re.IGNORECASE
    ), "⚠️ DELETE FROM without WHERE clause — this deletes ALL rows"),

    # ── Git Destruction ──
    ("git push --force", re.compile(
        r'\bgit\s+push\b.*\b--force\b(?!-with-lease)',
        re.IGNORECASE
    ), "⚠️ Force push overwrites remote history — use --force-with-lease instead"),

    ("git reset --hard", re.compile(
        r'\bgit\s+reset\b.*\b--hard\b',
        re.IGNORECASE
    ), "⚠️ Hard reset discards uncommitted changes permanently"),

    ("git clean -fd", re.compile(
        r'\bgit\s+clean\b.*\b-[fF][dD]',
        re.IGNORECASE
    ), "⚠️ Force clean removes all untracked files and directories"),

    # ── Permission / System ──
    ("chmod -R 777", re.compile(
        r'\bchmod\s+(?:-[A-Za-z]*[Rr][A-Za-z]*|--recursive)\s*7\d{2}\s',
        re.IGNORECASE
    ), "⚠️ Recursive 777 permissions — security risk, use specific permissions instead"),

    ("chown -R to nobody", re.compile(
        r'\bchown\s+(?:-[A-Za-z]*[Rr][A-Za-z]*|--recursive)\s+(?:nobody|65534)\s',
        re.IGNORECASE
    ), "⚠️ Recursive chown to nobody — can lock files from legitimate users"),

    # ── Shell Danger ──
    ("> /dev/sd*", re.compile(
        r'(?:^|[;&|`$()\s\n])(?:>|1>|2>)\s*/dev/(?:sd|hd|nvme|vd)',
        re.IGNORECASE
    ), "⚠️ Redirecting output to a raw block device — will corrupt the filesystem"),

    (":(){ :|:& };:", re.compile(
        r':\s*\(\s*\)\s*\{\s*:\s*\|',
        re.IGNORECASE
    ), "⚠️ Fork bomb detected — will crash the system by exhausting processes"),

    ("wget/curl pipe to bash", re.compile(
        r'(?:wget|curl)\b.*\|\s*(?:ba?sh|sh|zsh)',
        re.IGNORECASE
    ), "⚠️ Downloading and piping to shell — security risk, inspect the script first"),
]

# Additional dangerous patterns with simpler matching
SIMPLE_BLOCK_WORDS: list[str] = [
    "DROP DATABASE",
    "DROP SCHEMA",
    "REINDEX DATABASE",
    "VACUUM FULL",
    "pg_resetwal",
    "pg_dropbuffers",
]


@final
def block_reason(command: str, pattern_name: str, reason: str) -> str:
    """Format a clear block message."""
    return (
        f"\n"
        f"  ┌─────────────────────────────────────────────┐\n"
        f"  │  🛡️  BLOCKED: {pattern_name:<40}│\n"
        f"  ├─────────────────────────────────────────────┤\n"
        f"  │  {reason:<55}│\n"
        f"  ├─────────────────────────────────────────────┤\n"
        f"  │  Command: {command:<65.65}│\n"
        f"  └─────────────────────────────────────────────┘\n"
    )


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command is dangerous. Returns (is_blocked, reason)."""
    cmd_stripped = command.strip()

    # Check regex patterns
    for name, pattern, reason in BLOCK_PATTERNS:
        if pattern.search(cmd_stripped):
            return True, block_reason(command, name, reason)

    # Check simple word matches
    cmd_upper = cmd_stripped.upper()
    for word in SIMPLE_BLOCK_WORDS:
        if word in cmd_upper:
            return True, block_reason(command, word, f"⚠️ Potentially destructive database command — {word}")

    return False, ""


def log_block(command: str, reason: str) -> None:
    """Log blocked command to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    project = os.path.basename(os.getcwd()) if os.getcwd() else "unknown"
    entry = f"[{timestamp}] [{project}] BLOCKED: {command[:120]}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)
        if DETAILED_LOG:
            f.write(f"  Reason: {reason.strip()}\n")
        f.flush()


def main() -> int:
    """Main entry point — called by Claude Code as a pre-tool-use hook."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            # No input — allow (shouldn't happen in normal operation)
            return 0

        # Parse JSON payload from Claude Code
        try:
            payload = json.loads(raw_input)
        except json.JSONDecodeError:
            # Fallback: treat raw input as command
            blocked, reason = check_command(raw_input)
            if blocked:
                log_block(raw_input, reason)
                print(reason, file=sys.stderr)
                return 2
            return 0

        command = payload.get("command", "") or payload.get("args", "") or raw_input

        if not command:
            return 0

        blocked, reason = check_command(command)
        if blocked:
            log_block(command, reason)
            print(reason, file=sys.stderr)
            return 2

        return 0

    except Exception as e:
        # Fail open — if hook crashes, allow the command
        print(f"[hook] Warning: pre-tool-use hook error: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
