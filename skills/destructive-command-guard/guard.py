#!/usr/bin/env python3
"""PreToolUse hook that blocks destructive bash commands in Claude Code.

Reads JSON input from stdin, checks for dangerous patterns, logs blocks,
and returns a permission decision.

Patterns blocked:
  - rm -rf
  - DROP TABLE / DROP DATABASE
  - git push --force / git push -f / git push --force-with-lease
  - TRUNCATE TABLE / TRUNCATE
  - DELETE FROM without WHERE clause

Install: copy this script and settings.json into your project .claude/ directory.
See README.md for full setup instructions.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")


def _pattern_name() -> list[tuple[re.Pattern, str]]:
    return [
        (
            re.compile(r"\brm\s+-\S*[rf]\S*[rf]\S*\s", re.IGNORECASE),
            "rm -rf: destructive recursive force delete",
        ),
        (
            re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
            "DROP TABLE/DATABASE/SCHEMA: irreversible database object removal",
        ),
        (
            re.compile(r"\bgit\s+push\s+.*(--force\b|-f\b|--force-with-lease\b)", re.IGNORECASE),
            "git push --force/-f/--force-with-lease: rewrites remote history",
        ),
        (
            re.compile(r"\bTRUNCATE(\s+TABLE)?\b", re.IGNORECASE),
            "TRUNCATE: empties a table without a WHERE clause",
        ),
        (
            re.compile(r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", re.IGNORECASE | re.DOTALL),
            "DELETE FROM without WHERE: deletes all rows",
        ),
    ]


PATTERNS = _pattern_name()


def log_block(command: str, project_path: str, reason: str) -> None:
    log_dir = os.path.dirname(LOG_PATH)
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"{ts} | project={project_path} | reason={reason} | command={command}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(entry)


def check_command(command: str) -> str | None:
    for pattern, reason in PATTERNS:
        if pattern.search(command):
            return reason
    return None


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    reason = check_command(command)
    if reason is None:
        sys.exit(0)

    project_path = data.get("cwd", data.get("project_path", ""))
    log_block(command, project_path, reason)

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked by destructive-command-guard: {reason}. "
                    "If you are sure this is safe, ask the user to bypass the hook."
                ),
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()