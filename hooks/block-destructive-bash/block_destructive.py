#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook - Blocks destructive bash commands before execution.
Compatible with Claude Code hooks protocol.
Bounty Target: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3 ($100 USD)
Author: Chau Nghiep Phat (phatchau036)
"""
from __future__ import annotations
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Destructive pattern definitions
RM_RF_REGEX = re.compile(
    r"\brm\b.*(\s-[a-zA-Z]*[rR][a-zA-Z]*f[a-zA-Z]*\b|\s-[a-zA-Z]*f[a-zA-Z]*[rR][a-zA-Z]*\b|(\s(-r|-R|--recursive)\b.*\s(-f|--force)\b)|(\s(-f|--force)\b.*\s(-r|-R|--recursive)\b))"
)

RULES: list[tuple[str, re.Pattern]] = [
    ("DROP TABLE SQL statement", re.compile(r"\bDROP\s+(TABLE|DATABASE)\b", re.IGNORECASE)),
    ("TRUNCATE SQL statement", re.compile(r"\bTRUNCATE(\s+TABLE)?\b", re.IGNORECASE)),
    ("git push --force (unsafe force push)", re.compile(r"\bgit\s+push\b[^\n]*(\s--force(?!-with-lease)\b|\s-f\b)")),
    ("mkfs disk format", re.compile(r"\bmkfs(\.\w+)?\b")),
    ("dd write to raw device", re.compile(r"\bdd\b[^\n]*\bof=/dev/")),
    ("bash fork bomb", re.compile(r":\s*\(\s*\)\s*\{.*\}\s*;?\s*:")),
    ("recursive 777 permissions", re.compile(r"\bchmod\s+-R\s+777\b")),
]


def check_command_safety(cmd: str) -> str | None:
    """Inspect bash command string and return reason if dangerous, else None."""
    if not cmd or not cmd.strip():
        return None

    # Check rm -rf variants
    if RM_RF_REGEX.search(cmd):
        return "rm -rf (recursive force deletion)"

    # Check DELETE FROM without a WHERE clause
    cmd_lower = cmd.lower()
    if re.search(r"\bdelete\s+from\b", cmd_lower) and not re.search(r"\bwhere\b", cmd_lower):
        return "DELETE FROM without a WHERE clause"

    # Check remaining destructive rules
    for label, pattern in RULES:
        if pattern.search(cmd):
            return label

    return None


def write_log(reason: str, cmd: str, cwd: str) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat(timespec="seconds")
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{timestamp}\t{reason}\t{cmd.strip()}\t{cwd}\n")
    except Exception:
        pass


def main() -> int:
    """Entry point for PreToolUse hook."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return 0
        data = json.loads(raw_input)
    except Exception:
        # Fail open: never break Claude Code session on malformed hook payload
        return 0

    tool_name = data.get("tool_name") or data.get("tool") or ""
    if tool_name != "Bash":
        return 0

    tool_input = data.get("tool_input") or data.get("input") or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    cwd = data.get("cwd") or os.getcwd()

    violation = check_command_safety(command)
    if violation:
        write_log(violation, command, cwd)
        sys.stderr.write(
            f"\n[BLOCKED BY PRE-TOOL HOOK]\n"
            f"Pattern: {violation}\n"
            f"Command: {command}\n"
            f"Notice: Execution stopped to prevent destructive side-effects. "
            f"If this operation is intentional, please execute it manually outside Claude Code.\n"
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
