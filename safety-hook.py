#!/usr/bin/env python3
"""Pre-tool-use hook: blocks destructive bash commands before execution."""
import sys, json, os, re
from datetime import datetime

HOOK_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are ALWAYS blocked
BLOCKED_PATTERNS = [
    (r'rm\s+-rf\s', 'rm -rf (recursive force delete)'),
    (r'DROP\s+TABLE', 'DROP TABLE (destroys database table)'),
    (r'TRUNCATE\s+(TABLE\s+)?', 'TRUNCATE (removes all rows)'),
    (r'git\s+push\s+.*--force', 'git push --force (overwrites remote history)'),
    (r'git\s+push\s+.*-f', 'git push -f (force push)'),
    (r'DELETE\s+FROM\s+[\w.]+\s*$', 'DELETE FROM without WHERE clause'),
    (r'DELETE\s+FROM\s+[\w.]+\s*;', 'DELETE FROM without WHERE clause'),
    (r':\s*>\s*/dev/sda', 'raw disk write (destroys filesystem)'),
    (r'mkfs\.', 'mkfs (creates filesystem, destructive)'),
    (r'dd\s+if=', 'dd (disk duplicator, can overwrite disks)'),
    (r'>\s*/dev/', 'redirect to device file'),
    (r'chmod\s+777\b', 'chmod 777 (world-writable, security risk)'),
    (r'shutdown', 'system shutdown'),
    (r'reboot', 'system reboot'),
]

def log_blocked(command: str, project_path: str):
    os.makedirs(os.path.dirname(HOOK_LOG), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(HOOK_LOG, 'a') as f:
        f.write(f"[{timestamp}] BLOCKED | project={project_path} | command={command}\n")

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "block", "reason": "Invalid JSON input — blocking for safety"}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = os.getcwd()

    if tool_name != "Bash":
        print(json.dumps({"decision": "allow"}))
        return

    command = tool_input.get("command", "")

    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, project_path)
            print(json.dumps({
                "decision": "block",
                "reason": f"Blocked destructive command: {description}\n"
                          f"Command: {command}\n"
                          f"Logged to: {HOOK_LOG}\n"
                          f"To override this for legitimate use, remove the hook temporarily."
            }))
            return

    # Allow if no pattern matched
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
