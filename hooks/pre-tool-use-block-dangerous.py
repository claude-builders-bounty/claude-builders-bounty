#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: Block destructive bash commands."""

import sys
import json
import os
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    r'\brm\s+(-[rfRF]+\s+.*\S)',         # rm -rf / rm -fr with target
    r'\bDROP\s+TABLE\b',                   # SQL table drop
    r'\bTRUNCATE\s+TABLE?\b',              # SQL truncate
    r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',   # DELETE without WHERE
    r'\bgit\s+push\s+(-f|--force)',        # Force push
    r'\b:\(\)\s*\{.*\}.*;',                # Fork bomb
    r'\b>\s*/dev/sd[a-z]',                 # Disk overwrite
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command, reason, project):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {project} | {reason} | {command}\n")

def check_command(command):
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, pattern
    return True, ""

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("project_path", "unknown")

    if tool_name not in ("bash", "run", "exec"):
        sys.exit(0)

    command = tool_input.get("command", "") or tool_input.get("code", "")
    if not command:
        sys.exit(0)

    allowed, reason = check_command(command)
    if not allowed:
        log_blocked(command, reason, project_path)
        result = json.dumps({
            "decision": "reject",
            "reason": "Blocked destructive command: " + reason +
                      ". Logged to " + LOG_FILE
        })
        print(result)
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()