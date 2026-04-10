#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Block destructive bash commands.

Install:
  mkdir -p ~/.claude/hooks
  cp pre-tool-use-blocker.py ~/.claude/hooks/pre-tool-use-blocker.py
  chmod +x ~/.claude/hooks/pre-tool-use-blocker.py

Claude Code will automatically discover and run hooks from ~/.claude/hooks/.
"""

import sys
import json
import re
import os
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that represent dangerous operations.
DANGEROUS_PATTERNS = [
    (r'rm\s+-rf\s+/\s',                  "refusing to recursively delete root filesystem"),
    (r'rm\s+-rf\s+\.\s*$',               "recursive delete of current directory"),
    (r'rm\s+-rf\s+\"',                   "recursive delete with quoted path"),
    (r'rm\s+-rf\s+\'',                   "recursive delete with single-quoted path"),
    (r'mv\s+.*\s+/dev/null',             "moving file to /dev/null (data destruction)"),
    (r'>\s*/etc/',                        "redirecting to /etc (system config destruction)"),
    (r'>\s*/sys/',                        "redirecting to /sys (kernel interface)"),
    (r'>\s*/proc/',                       "redirecting to /proc (kernel interface)"),
    (r'git\s+push\s+--force\s',          "git push --force (rewrites shared remote history)"),
    (r'git\s+push\s+-f\s',               "git push -f (force push)"),
    (r'git\s+push\s+--force-with-lease', "git force-with-lease (still risky)"),
    (r'DROP\s+TABLE',                     "DROP TABLE (deletes entire table)"),
    (r'DROP\s+DATABASE',                  "DROP DATABASE (deletes entire database)"),
    (r'DROP\s+SCHEMA',                    "DROP SCHEMA (deletes entire schema)"),
    (r'TRUNCATE\s+',                      "TRUNCATE (deletes all rows from table)"),
    (r'DELETE\s+FROM\s+\w+\s*;\s*$',     "DELETE without WHERE clause (deletes all rows)"),
    (r'DELETE\s+FROM\s+\w+\s+LIMIT',     "DELETE with LIMIT but no WHERE (bulk deletion risk)"),
    (r'history\s+-c',                     "clearing shell history"),
    (r'>\s*~/.bash_history',              "truncating bash history"),
    (r'apt-get\s+purge',                 "apt-get purge (removes packages + configs)"),
]

COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), msg) for p, msg in DANGEROUS_PATTERNS]


def log_blocked(command: str, project_path: str, reason: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = (
        f"[{timestamp}] BLOCKED command in {project_path}: {command!r}\n"
        f"  Reason: {reason}\n"
    )
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass


def check_command(command: str) -> tuple[bool, str | None]:
    for pattern, reason in COMPILED_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, None


def main() -> None:
    """
    Claude Code hooks receive JSON on stdin:
      { "tool_name": "...", "tool_input": {...}, "project_path": "..." }

    Exit 0   = allow
    Exit 33  = block (Claude Code convention for pre-tool-use block)
    """
    try:
        raw = sys.stdin.read()
        if not raw:
            sys.exit(0)
        payload = json.loads(raw)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = payload.get("project_path", os.getcwd())

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, project_path, reason)
        block_msg = (
            f"\n HOOK BLOCKED: {reason}\n"
            f"   Command: {command!r}\n"
            f"   Project: {project_path}\n"
            f"   Logged to: {LOG_FILE}\n"
        )
        sys.stderr.write(block_msg)
        sys.stderr.flush()
        sys.exit(33)

    sys.exit(0)


if __name__ == "__main__":
    main()
