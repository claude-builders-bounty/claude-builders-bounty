#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Blocks dangerous bash commands before they are executed by Claude Code.

Install: see README.md
"""

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Each entry is (label, pattern).
# Patterns are matched case-insensitively against the full command string.
BLOCKED_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "rm -rf (recursive force delete)",
        re.compile(r"\brm\b.*\s-[a-zA-Z]*r[a-zA-Z]*f|rm\b.*\s-[a-zA-Z]*f[a-zA-Z]*r", re.IGNORECASE),
    ),
    (
        "rm -rf shorthand",
        re.compile(r"\brm\s+-rf\b|\brm\s+--recursive\s+--force\b|\brm\s+-fr\b", re.IGNORECASE),
    ),
    (
        "DROP TABLE (destructive SQL)",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    ),
    (
        "TRUNCATE (destructive SQL)",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    ),
    (
        "DELETE FROM without WHERE (deletes all rows)",
        re.compile(r"\bDELETE\s+FROM\s+\S+\s*(?:;|$)", re.IGNORECASE),
    ),
    (
        "git push --force / -f (overwrites remote history)",
        re.compile(r"\bgit\s+push\b.*(?:--force|-f\b|--force-with-lease)", re.IGNORECASE),
    ),
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def log_blocked(command: str, reason: str, project_path: str) -> None:
    logging.info(
        "BLOCKED | reason=%r | project=%r | command=%r",
        reason,
        project_path,
        command,
    )


# ---------------------------------------------------------------------------
# Hook logic
# ---------------------------------------------------------------------------

def get_project_path() -> str:
    """Return the current working directory (best proxy for project path)."""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def check_command(command: str) -> tuple[bool, str]:
    """
    Returns (blocked: bool, reason: str).
    Only the first matching pattern is reported.
    """
    for label, pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, label
    return False, ""


def build_denial_message(command: str, reason: str) -> str:
    return (
        f"🚫 BLOCKED by safety hook\n"
        f"Reason : {reason}\n"
        f"Command: {command!r}\n\n"
        f"This command has been blocked because it can cause irreversible data loss. "
        f"If you genuinely need to run a destructive operation, please ask the user to "
        f"do it manually after reviewing the consequences.\n"
        f"Blocked attempt has been logged to {LOG_FILE}"
    )


def main() -> None:
    setup_logging()

    # Claude Code sends tool input as JSON on stdin.
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If stdin is not valid JSON, allow the command through
        # (this hook only targets the Bash tool).
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Only inspect Bash / Shell tool calls
    if tool_name not in ("Bash", "Shell", "bash", "shell"):
        sys.exit(0)

    command = tool_input.get("command", "") or tool_input.get("cmd", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)

    if blocked:
        project_path = get_project_path()
        log_blocked(command, reason, project_path)
        # Output the denial message so Claude sees it
        print(build_denial_message(command, reason), flush=True)
        sys.exit(1)  # non-zero exit = blocked

    # Command is safe — exit 0, no output, Claude proceeds normally
    sys.exit(0)


if __name__ == "__main__":
    main()
