#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    r"\brm\s+-[rRfF]+\b",
    r"\bDROP\s+TABLE\b",
    r"\bgit\s+push\s+.*--force",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b)"
]

def is_destructive(command: str) -> bool:
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def log_blocked_attempt(command: str, project_path: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"{timestamp} | Project: {project_path} | Command: {command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_use = input_data.get("tool_use", {})
    tool_name = tool_use.get("name")
    
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = tool_use.get("input", {})
    command = tool_input.get("command", "")
    project_path = input_data.get("project_path", os.getcwd())

    if is_destructive(command):
        log_blocked_attempt(command, project_path)
        
        response = {
            "decision": "block",
            "message": (
                f"Action blocked: The command '{command}' matches a restricted destructive pattern "
                "(e.g., recursive deletion, unconstrained table drop, or forced push). "
                "Please revise your approach to ensure data safety."
            )
        }
        print(json.dumps(response))
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
