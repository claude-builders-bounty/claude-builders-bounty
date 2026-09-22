#!/usr/bin/env python3
"""
pre-tool-use.py - Claude Code Hook: Block Destructive Bash Commands

Intercepts bash/shell tool executions in Claude Code to prevent destructive
operations (e.g. recursive removals, force pushes, unrestricted SQL drops/deletes).
Logs all blocked events to ~/.claude/hooks/blocked.log.
"""

import datetime
import json
import os
import re
import sys
from pathlib import Path

# Destructive command patterns to block
BLOCKED_PATTERNS = [
    (
        r"\brm\s+(?:-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)[a-zA-Z]*|-(?:r|R)\s+-[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*\s+-(?:r|R)|--recursive\s+--force|--force\s+--recursive)\b",
        "Recursive force removal (`rm -rf` / `--recursive --force`) is dangerous and prohibited."
    ),
    (
        r"\bDROP\s+TABLE\b",
        "Destructive database modification (`DROP TABLE`) is prohibited via automated tools."
    ),
    (
        r"\bTRUNCATE(?:\s+TABLE)?\b",
        "Destructive database truncation (`TRUNCATE TABLE`) is prohibited."
    ),
    (
        r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b)",
        "Unrestricted `DELETE FROM` without a `WHERE` clause will wipe the entire table."
    ),
    (
        r"\bgit\s+push\s+.*(?:--force|-f\b|\+[a-zA-Z0-9_\-\./]+)",
        "Force pushing (`git push --force` / `-f`) can overwrite remote repository history."
    ),
    (
        r"\bmkfs\b|\bfdisk\b|\bdd\s+if=.*of=/dev/",
        "Disk partitioning and raw block device overwriting are prohibited."
    ),
    (
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
        "Fork bomb execution detected and blocked."
    )
]


def get_log_file_path() -> Path:
    home_claude_hooks = Path.home() / ".claude" / "hooks"
    home_claude_hooks.mkdir(parents=True, exist_ok=True)
    return home_claude_hooks / "blocked.log"


def log_blocked_event(command: str, reason: str, cwd: str):
    log_file = get_log_file_path()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Project Path: {cwd}\n"
        f"  Command:      {command}\n"
        f"  Reason:       {reason}\n"
        f"{'-' * 60}\n"
    )
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[Hook Warning] Could not write to blocked.log: {e}\n")


def inspect_command(command: str) -> tuple[bool, str]:
    """
    Checks if command matches any destructive pattern.
    Returns (is_blocked, reason).
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def process_hook_input(raw_input: str) -> int:
    """
    Parses Claude Code pre-tool-use payload.
    Supports both JSON payload from stdin and raw command-line string.
    """
    command = ""
    tool_name = ""
    cwd = os.getcwd()

    try:
        data = json.loads(raw_input)
        tool_name = data.get("tool_name", "") or data.get("tool", "")
        tool_input = data.get("tool_input", {})

        if isinstance(tool_input, dict):
            command = tool_input.get("command", "") or tool_input.get("cmd", "") or tool_input.get("CommandLine", "")
        elif isinstance(tool_input, str):
            command = tool_input

        if data.get("cwd"):
            cwd = data.get("cwd")
    except Exception:
        # Fallback to treating input as plain command string
        command = raw_input.strip()

    if not command:
        return 0  # No command to inspect

    is_blocked, reason = inspect_command(command)
    if is_blocked:
        log_blocked_event(command, reason, cwd)
        error_message = (
            f"\n🚨 [Claude Code Security Hook] Execution Blocked!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Attempted Command: {command}\n"
            f"Policy Violation:  {reason}\n"
            f"Log Recorded:      {get_log_file_path()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        sys.stderr.write(error_message)
        # Exit with code 2 to inform Claude Code tool execution is rejected
        return 2

    return 0


def main():
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    else:
        raw_input = sys.stdin.read()

    exit_code = process_hook_input(raw_input)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
