#!/usr/bin/env python3
"""Pre-tool-use hook: blocks destructive bash commands before execution."""
import json, sys, re, os
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', 'Destructive delete (rm -rf)'),
    (r'\bDROP\s+TABLE\b', 'SQL DROP TABLE'),
    (r'\bDROP\s+DATABASE\b', 'SQL DROP DATABASE'),
    (r'\bgit\s+push\s+--force\b', 'Force push to remote'),
    (r'\bgit\s+push\s+-f\b', 'Force push to remote'),
    (r'\bTRUNCATE\s+(TABLE\s+)?', 'SQL TRUNCATE'),
    (r'\bDELETE\s+FROM\s+\w+\s*$', 'SQL DELETE without WHERE'),
    (r'\bDELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1', 'SQL DELETE all rows'),
    (r':\s*>\s*/dev/sd[a-z]', 'Write to raw disk device'),
    (r'\bchmod\s+-R\s+777\b', 'World-writable recursive chmod'),
    (r'\bcurl.*\|\s*(ba)?sh\b', 'Pipe curl to shell'),
    (r'\bwget.*-O\s*-\s*\|\s*(ba)?sh\b', 'Pipe wget to shell'),
]

def log_blocked(command, reason):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command[:500],
        "reason": reason
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason)
            print(json.dumps({
                "decision": "block",
                "reason": f"BLOCKED: {reason}. This command matches the safety blocklist."
            }))
            sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
