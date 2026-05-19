#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands."""

import json, os, re, sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.expanduser("~/.claude/hooks")

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-rf\b', 'Recursive force delete — irreversible file deletion'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE — deletes entire table with all data'),
    (r'\bgit\s+push\s+.*--force\b', 'Git force push — overwrites remote history'),
    (r'\bgit\s+push\s+.*-f\b', 'Git force push (-f) — overwrites remote history'),
    (r'\bTRUNCATE\b', 'TRUNCATE — deletes all rows without rollback'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM without WHERE — deletes all rows'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE — destroys entire database'),
    (r'\bchmod\s+-R\s+777\b', 'World-writable permissions — security risk'),
]


def log_blocked(command: str, project_path: str = ""):
    os.makedirs(HOOK_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
        "project_path": project_path or os.getcwd(),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_destructive(command: str):
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("Bash", "bash", "terminal"):
        print(json.dumps({"continue": True}))
        return

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"continue": True}))
        return

    is_destructive, description = check_destructive(command)

    if is_destructive:
        log_blocked(command, os.getcwd())
        print(json.dumps({
            "continue": False,
            "reason": (
                f"BLOCKED: {description}\n"
                f"Command: {command}\n"
                f"This command could cause irreversible data loss.\n"
                f"Use a safer alternative or manually approve.\n"
                f"Blocked attempt logged to: {LOG_FILE}"
            )
        }))
        return

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
