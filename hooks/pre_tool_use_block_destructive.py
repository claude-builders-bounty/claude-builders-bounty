#!/usr/bin/env python3
"""Pre-tool-use hook for Claude Code to block destructive bash commands.

Blocks execution of:
- `rm -rf` (and equivalent force-recursive directory removal)
- `DROP TABLE` statements
- `git push --force` / `git push -f`
- `TRUNCATE` statements
- `DELETE FROM` without a `WHERE` clause

Logs blocked attempts to `~/.claude/hooks/blocked.log`.
"""

from datetime import datetime, timezone
import json
import os
import re
import sys

DEFAULT_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")
LOG_PATH = os.environ.get("BLOCKED_LOG_PATH", DEFAULT_LOG_PATH)

DESTRUCTIVE_PATTERNS = [
    (
        re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b|\brm\s+--recursive\s+--force\b|\brm\s+--force\s+--recursive\b", re.IGNORECASE),
        "Recursive force removal (`rm -rf`) is destructive and prohibited.",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "SQL `DROP TABLE` command detected.",
    ),
    (
        re.compile(r"\bgit\s+push\s+.*(--force|-f|--force-with-lease)\b", re.IGNORECASE),
        "Force pushing to git (`git push --force`) is prohibited.",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_.]+\b", re.IGNORECASE),
        "SQL `TRUNCATE` command detected.",
    ),
]

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def is_destructive(command: str) -> tuple[bool, str]:
    """Check if a bash command contains any destructive patterns."""
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, reason

    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return True, "SQL `DELETE FROM` statement without a `WHERE` clause detected."

    return False, ""


def log_blocked(command: str, cwd: str, reason: str) -> None:
    """Log blocked command execution attempt to logfile."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] CWD: {cwd} | REASON: {reason} | COMMAND: {command}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked log: {e}\n")


def main() -> int:
    """Read Claude Code hook JSON input from stdin and evaluate command safety."""
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        return 0

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        # If input is not JSON, check raw text as fallback command string
        data = {"tool_name": "Bash", "tool_input": {"command": raw_input}}

    tool_name = data.get("tool_name", "")
    if tool_name.lower() not in ("bash", "execute_command", "command"):
        return 0

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
    cwd = data.get("cwd", os.getcwd())

    blocked, reason = is_destructive(command)
    if blocked:
        log_blocked(command, cwd, reason)
        error_msg = (
            f"[SECURITY HOOK BLOCKED]\n"
            f"Command blocked for safety: '{command}'\n"
            f"Reason: {reason}\n"
            f"Execution halted by Claude Code pre-tool-use security hook."
        )
        sys.stderr.write(error_msg + "\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
