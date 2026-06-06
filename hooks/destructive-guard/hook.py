#!/usr/bin/env python3
"""
pre-tool-use hook: blocks destructive bash commands before execution.

Install: copy to ~/.claude/hooks/pre-tool-use/destructive-guard.py
Claude Code calls this hook before every tool use with JSON on stdin.
Exit 0 = allow, exit 2 = block (Claude sees the message).
"""

import json
import re
import sys
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Each entry: (pattern, reason, case_insensitive)
BLOCKED_PATTERNS = [
    # rm -rf / rm -fr / rm -Rf etc. — any combo of -r and -f flags (case insensitive on flags)
    (r'\brm\s+(-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*)(\s|$)', "rm -rf (recursive force delete)", False),
    # DROP TABLE (SQL, case insensitive)
    (r'\bDROP\s+TABLE\b', "DROP TABLE (destroys database table)", True),
    # git push --force / -f
    (r'\bgit\s+push\b.*\s(--force|-f)\b', "git push --force (overwrites remote history)", False),
    # TRUNCATE (SQL, case insensitive)
    (r'\bTRUNCATE\b', "TRUNCATE (empties database table)", True),
    # DELETE FROM without WHERE (case insensitive, dotall so newlines don't bypass)
    (r'\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)', "DELETE FROM without WHERE (deletes all rows)", True),
]


def log_blocked(command: str, reason: str, tool_name: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"{ts} | tool={tool_name} | reason={reason} | cmd={command!r} | project={project_path}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason)."""
    for pattern, reason, case_insensitive in BLOCKED_PATTERNS:
        flags = (re.IGNORECASE | re.DOTALL) if case_insensitive else re.DOTALL
        if re.search(pattern, command, flags):
            return True, reason
    return False, ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Not JSON input — allow through
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only inspect Bash/shell tool calls
    if tool_name not in ("Bash", "bash", "shell", "run_bash", "execute_bash"):
        return 0

    command = tool_input.get("command", tool_input.get("cmd", ""))
    if not command:
        return 0

    blocked, reason = check_command(command)
    if not blocked:
        return 0

    log_blocked(command, reason, tool_name)

    message = (
        f"🚫 BLOCKED: {reason}\n\n"
        f"The command `{command[:120]}{'...' if len(command) > 120 else ''}` "
        f"matches a destructive pattern and was prevented from running.\n\n"
        f"If this was intentional, ask the user for explicit confirmation before retrying. "
        f"This block has been logged to {LOG_FILE}."
    )
    print(json.dumps({"decision": "block", "reason": message}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
