#!/usr/bin/env python3
"""Pre-tool-use hook: block destructive bash commands.

Claude Code invokes this script with the tool payload on stdin (JSON).
Exit 0 = allow, non-zero = block (stderr is shown to Claude).
"""
import json
import os
import re
import sys
from datetime import datetime

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"rm\s+-rf", re.IGNORECASE), "rm -rf (recursive force delete)"),
    (re.compile(r"DROP\s+TABLE", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"git\s+push\s+--force", re.IGNORECASE), "git push --force"),
    (re.compile(r"TRUNCATE", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"DELETE\s+FROM\s+\w+\s*;?\s*$", re.IGNORECASE), "DELETE FROM without WHERE"),
    (re.compile(r"DELETE\s+FROM\s+\w+\s*$", re.IGNORECASE), "DELETE FROM without WHERE"),
]


def log_blocked(command: str, project: str, reason: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {project} | {reason} | {command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Not a tool payload we understand; allow.
        return 0

    tool_name = payload.get("tool_name") or payload.get("name") or ""
    if tool_name not in ("Bash", "bash", "shell"):
        return 0

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        return 0

    project = os.getcwd()

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            log_blocked(command, project, reason)
            sys.stderr.write(
                f"Blocked by pre-tool-use hook: '{reason}' detected.\n"
                f"Command: {command}\n"
                f"Reason: this operation is destructive and potentially irreversible.\n"
                f"If you are sure, run it manually outside of Claude Code.\n"
            )
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())