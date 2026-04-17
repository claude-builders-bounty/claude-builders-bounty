#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks dangerous bash commands.
Reads JSON from stdin, inspects Bash tool calls, and exits 2 to block
commands matching destructive patterns.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

PATTERNS = [
    (re.compile(r"\brm\s+-[^\s]*r[^\s]*\s+-[^\s]*f|rm\s+-[^\s]*f[^\s]*\s+-[^\s]*r|\brm\s+-rf\b|\brm\s+-fr\b", re.IGNORECASE), "rm -rf (recursive force delete)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bgit\s+push\s+(?:.*\s)?--force\b|\bgit\s+push\s+(?:.*\s)?-f\b", re.IGNORECASE), "git push --force"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", re.IGNORECASE), "DELETE FROM without WHERE"),
]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = f"[{timestamp}] BLOCKED({reason}) path={project_path!r} cmd={command!r}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> str | None:
    for pattern, label in PATTERNS:
        if pattern.search(command):
            return label
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Bash", "bash"):
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "") or tool_input.get("cmd", "")
    if not command:
        sys.exit(0)

    reason = check_command(command)
    if reason is None:
        sys.exit(0)

    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    log_blocked(command, reason, project_path)

    print(
        f"BLOCKED: This command was blocked by the safety hook.\n"
        f"Reason: matches dangerous pattern '{reason}'.\n"
        f"Command: {command!r}\n"
        f"If this was intentional, run the command directly in your terminal."
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
