#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    (r"\brm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b", "Recursive forced deletion (rm -rf)"),
    (r"\bDROP\s+TABLE\b", "SQL DROP TABLE command"),
    (r"\bgit\s+push\s+(?:.*?\s+)?(?:--force|-f)\b", "Forced git push (git push --force)"),
    (r"\bTRUNCATE\b", "SQL TRUNCATE command"),
    (r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b)", "Unrestricted SQL DELETE statement without WHERE clause")
]

def check_command(cmd: str):
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return desc
    return None

def log_blocked(cmd: str, project_path: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] PROJECT: {project_path} | COMMAND: {cmd}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Not JSON or empty stdin, allow execution
        sys.exit(0)

    tool_name = data.get("tool", "")
    tool_input = data.get("input", {})

    cmd = ""
    if tool_name in ["bash", "execute_command", "run_command", "terminal"]:
        cmd = tool_input.get("command", "") or tool_input.get("cmd", "")
    elif "command" in tool_input:
        cmd = tool_input.get("command", "")

    if not cmd:
        sys.exit(0)

    reason = check_command(cmd)
    if reason:
        project_path = data.get("cwd", os.getcwd())
        log_blocked(cmd, project_path)
        print(f"[BLOCKED] Destructive command detected ({reason}): '{cmd}'", file=sys.stderr)
        print(f"Action blocked by safety policy. Logged to {LOG_FILE}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
