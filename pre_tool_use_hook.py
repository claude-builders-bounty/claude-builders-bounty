#!/usr/bin/env python3
import json, os, re, sys
from datetime import datetime, timezone

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")
DESTRUCTIVE_PATTERNS = [
    (re.compile(r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|.*-rf)\b'), "rm -rf detected"),
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE detected"),
    (re.compile(r'\bgit\s+push\s+.*--force\b'), "git push --force detected"),
    (re.compile(r'\bTRUNCATE\b', re.IGNORECASE), "TRUNCATE detected"),
]
DELETE_NO_WHERE = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)
WHERE_CLAUSE = re.compile(r'\bWHERE\b', re.IGNORECASE)

def check_destructive(command):
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return reason
    if DELETE_NO_WHERE.search(command) and not WHERE_CLAUSE.search(command):
        return "DELETE FROM without WHERE clause detected"
    return None

def log_blocked(command, reason, project_path):
    os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(BLOCKED_LOG, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n\n")

def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    if input_data.get("tool_name") != "Bash":
        sys.exit(0)
    command = input_data.get("input", {}).get("command", "")
    if not command:
        sys.exit(0)
    project_path = input_data.get("cwd", os.getcwd())
    reason = check_destructive(command)
    if reason:
        log_blocked(command, reason, project_path)
        print(f"⛔ BLOCKED: {reason}\n\nThis command was blocked by the destructive-command-guard hook.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
