#!/usr/bin/env python3
"""Pre-tool-use hook for Claude Code - blocks destructive bash commands."""

import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

DESTRUCTIVE_PATTERNS = [
    (re.compile(r'\brm\s+-[rRfF]+', re.IGNORECASE), "rm -rf recursive force delete"),
    (re.compile(r'\brm\s+--recursive\s+--force\b', re.IGNORECASE), "rm --recursive --force delete"),
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE destructive database operation"),
    (re.compile(r'\bgit\s+push\s+.*--force\b', re.IGNORECASE), "git push --force force push"),
    (re.compile(r'\bgit\s+push\s+.*-f\b', re.IGNORECASE), "git push -f force push"),
    (re.compile(r'\bTRUNCATE\b', re.IGNORECASE), "TRUNCATE destructive table operation"),
    (re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE), "DELETE FROM unqualified delete"),
]

DELETE_WHERE = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)


def extract_command(tool_input):
    if isinstance(tool_input, dict):
        return tool_input.get("command", "")
    if isinstance(tool_input, str):
        return tool_input
    return str(tool_input) if tool_input else ""


def has_where_clause(command):
    after = DELETE_WHERE.sub("", command, count=1)
    return bool(re.search(r'\bWHERE\b', after, re.IGNORECASE))


def check_destructive(command):
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            if "DELETE FROM" in reason.upper():
                if has_where_clause(command):
                    continue
            return True, reason
    return False, ""


def log_blocked(command, project_path):
    os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(BLOCKED_LOG, "a") as f:
        f.write(f"[{ts}] command={command!r} project={project_path!r}\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"allowed": True}))
        return

    tool_input = data.get("input", {})
    command = extract_command(tool_input)
    project_path = ""
    if isinstance(tool_input, dict):
        project_path = tool_input.get("cwd", "") or os.getcwd()
    if not command:
        command = data.get("command", "")
    if not project_path:
        project_path = os.getcwd()

    blocked, reason = check_destructive(command)
    if blocked:
        log_blocked(command, project_path)
        print(json.dumps({"allowed": False, "message": f"BLOCKED: {reason}\nCommand: {command}"}))
    else:
        print(json.dumps({"allowed": True}))


if __name__ == "__main__":
    main()
