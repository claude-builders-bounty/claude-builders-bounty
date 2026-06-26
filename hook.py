#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Blocks dangerous bash commands before execution.
"""
import re
import sys
import json
import os
from datetime import datetime

BLOCKED_PATTERNS = [
    (r'rm\s+(-[a-zA-Z]*\s+)*-?-\s*rf\b', "rm -rf (recursive force delete)"),
    (r'rm\s+(-[a-zA-Z]*\s+)*-?-\s*fr\b', "rm -fr (recursive force delete)"),
    (r'DROP\s+TABLE\b', "DROP TABLE (destructive SQL)"),
    (r'git\s+push\s+.*--force\b', "git push --force (force push)"),
    (r'git\s+push\s+.*-f\b', "git push -f (force push)"),
    (r'TRUNCATE\s+TABLE\b', "TRUNCATE TABLE (destructive SQL)"),
    (r'DELETE\s+FROM\b(?![\s\S]*WHERE)', "DELETE FROM without WHERE clause"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command, reason, project_path):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n")
        f.write(f"  Command: {command}\n")
        f.write(f"  Project: {project_path}\n\n")


def check_command(command):
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    command = input_data.get("command", "")
    tool_name = input_data.get("tool_name", "")

    if tool_name != "Bash":
        sys.exit(0)

    project_path = os.getcwd()
    reason = check_command(command)

    if reason:
        log_blocked(command, reason, project_path)
        print(json.dumps({
            "decision": "block",
            "reason": f"Blocked by destructive-command-hook: {reason}"
        }))
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
