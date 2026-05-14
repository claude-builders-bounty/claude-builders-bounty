#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime, timezone

# Blocked patterns (logic)
def is_destructive(command):
    cmd_lower = command.lower().strip()

    # 1. rm -rf variations
    if cmd_lower.startswith('rm ') or ' rm ' in cmd_lower:
        # Check for recursive flag
        has_recursive = re.search(r'\s-(?:[^-]*r|r[^-]*)\b', cmd_lower) or '--recursive' in cmd_lower
        # Check for force flag
        has_force = re.search(r'\s-(?:[^-]*f|f[^-]*)\b', cmd_lower) or '--force' in cmd_lower

        if has_recursive and has_force:
            return "Recursive force delete (rm -rf) is blocked to prevent irreversible data loss."

    # 2. git push --force variations
    if 'git push' in cmd_lower:
        if re.search(r'\s-(?:[^-]*f|f[^-]*)\b', cmd_lower) or '--force' in cmd_lower:
            return "Git force push is blocked to protect remote repository history."

    # 3. SQL destruction
    if re.search(r'\bdrop\s+(?:table|database)\b', cmd_lower):
        return "SQL DROP command is blocked to prevent data destruction."

    if re.search(r'\btruncate\b', cmd_lower):
        if not re.search(r'\btruncate\s+log\b', cmd_lower):
             return "SQL TRUNCATE command is blocked to prevent data destruction."

    if re.search(r'\bdelete\s+from\s+', cmd_lower) and not re.search(r'\bwhere\b', cmd_lower):
        return "SQL DELETE without a WHERE clause is blocked to prevent mass row deletion."

    return None

def log_blocked(command, pattern_msg):
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "reason": pattern_msg,
        "project_path": os.getcwd()
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    try:
        hook_input = sys.stdin.read()
        if not hook_input:
            sys.exit(0)

        data = json.loads(hook_input)

        if data.get("tool") != "bash":
            print(json.dumps({"action": "allow"}))
            return

        command = data.get("arguments", {}).get("command", "")

        reason = is_destructive(command)
        if reason:
            log_blocked(command, reason)
            print(json.dumps({
                "action": "deny",
                "message": f"COMMAND BLOCKED: {reason}\nAttempted command: {command}"
            }))
            return

        print(json.dumps({"action": "allow"}))

    except Exception as e:
        sys.stderr.write(f"Hook error: {str(e)}\n")
        print(json.dumps({"action": "allow"}))

if __name__ == "__main__":
    main()
