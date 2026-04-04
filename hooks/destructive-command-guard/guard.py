#!/usr/bin/env python3
"""
Destructive Command Guard — Claude Code pre-tool-use hook.

Intercepts dangerous bash commands before execution and blocks them
with a clear explanation. All blocked attempts are logged.

Install:
    cp guard.py ~/.claude/hooks/pre-tool-use/
    chmod +x ~/.claude/hooks/pre-tool-use/guard.py

Or one-liner:
    mkdir -p ~/.claude/hooks/pre-tool-use && cp guard.py ~/.claude/hooks/pre-tool-use/ && chmod +x ~/.claude/hooks/pre-tool-use/guard.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# ---------------------------------------------------------------------------
# Dangerous patterns — each tuple is (compiled_regex, human_description)
# ---------------------------------------------------------------------------
PATTERNS = [
    # Filesystem destruction
    (re.compile(r"\brm\s+.*-\s*[^\s]*r[^\s]*f|rm\s+.*-\s*[^\s]*f[^\s]*r|\brm\s+-rf\b", re.I),
     "rm -rf: recursive forced deletion can destroy entire directory trees"),

    (re.compile(r"\brm\s+.*-\s*[^\s]*r\b.*\s+(/\s*$|~|\*|\.\.)"),
     "recursive rm with broad path target (/, ~, *, ..)"),

    # SQL destructive operations
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\s+\w", re.I),
     "DROP TABLE/DATABASE: permanently removes database objects"),

    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w", re.I),
     "TRUNCATE: removes all rows from a table instantly"),

    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;?\s*$", re.I | re.M),
     "DELETE FROM without WHERE clause: deletes ALL rows in the table"),

    (re.compile(r"\bDELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1", re.I),
     "DELETE FROM ... WHERE 1=1: effectively deletes all rows"),

    # Git force operations
    (re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+-f\b", re.I),
     "git push --force: rewrites remote history, can destroy others' work"),

    (re.compile(r"\bgit\s+clean\s+.*-\s*[^\s]*f[^\s]*d|\bgit\s+clean\s+.*-\s*[^\s]*d[^\s]*f", re.I),
     "git clean -fd: permanently removes untracked files and directories"),

    (re.compile(r"\bgit\s+reset\s+--hard\b", re.I),
     "git reset --hard: discards all uncommitted changes permanently"),

    # System-level destruction
    (re.compile(r"\bmkfs\b", re.I),
     "mkfs: formats a filesystem, destroying all data on the device"),

    (re.compile(r"\bdd\s+.*of\s*=\s*/dev/", re.I),
     "dd writing to device: can overwrite disk partitions"),

    (re.compile(r">\s*/dev/sd[a-z]|>\s*/dev/nvme", re.I),
     "redirecting output to a block device: overwrites disk data"),

    # chmod/chown nuclear options
    (re.compile(r"\bchmod\s+.*-R\s+.*777\s+/\s*$", re.I),
     "chmod -R 777 /: opens all permissions on the entire filesystem"),

    (re.compile(r"\bchown\s+.*-R\s+.*\s+/\s*$", re.I),
     "chown -R on /: changes ownership of the entire filesystem"),

    # Container/environment destruction
    (re.compile(r"\bdocker\s+system\s+prune\s+-a", re.I),
     "docker system prune -a: removes ALL unused images, containers, networks"),

    # Environment variable destruction (fork bomb, etc.)
    (re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;", re.I),
     "fork bomb: crashes the system by spawning infinite processes"),
]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked-attempt record to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "project_path": project_path,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str) -> tuple:
    """Return (is_blocked, reason) for a given command string."""
    for pattern, description in PATTERNS:
        if pattern.search(command):
            return True, description
    return False, ""


def main() -> None:
    """
    Claude Code hook entry point.

    Reads the tool-use event from stdin (JSON), inspects the command,
    and exits with code 2 + a JSON error message to block execution,
    or exits 0 to allow it.
    """
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Can't parse — allow (fail open)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Only inspect bash/shell tool uses
    if tool_name not in ("bash", "shell", "terminal", "execute_command"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)

    if blocked:
        project_path = event.get("project_path", os.getcwd())
        log_blocked(command, reason, project_path)

        # Return structured error for Claude to understand
        error = {
            "blocked": True,
            "reason": reason,
            "command": command,
            "message": (
                f"BLOCKED: This command was intercepted by the Destructive Command Guard.\n"
                f"Reason: {reason}\n"
                f"Command: {command}\n\n"
                f"If you believe this is safe, ask the user to run it manually or "
                f"modify the command to be more targeted."
            ),
        }
        print(json.dumps(error))
        sys.exit(2)  # Non-zero exit blocks the tool use

    sys.exit(0)


if __name__ == "__main__":
    main()
