#!/usr/bin/env python3
import sys
import os
import json
import re
import datetime

# Path to log file
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def find_command(obj):
    """Recursively search a JSON structure for the 'command' key."""
    if isinstance(obj, dict):
        if "command" in obj:
            return obj["command"]
        for v in obj.values():
            res = find_command(v)
            if res is not None:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_command(item)
            if res is not None:
                return res
    return None

def check_destructive(cmd: str):
    """
    Evaluates if the command contains any destructive patterns.
    Returns (is_destructive: bool, reason_message: str)
    """
    # 1. rm -rf
    if re.search(r'\brm\b', cmd):
        # Check for recursive option: -r, -R, or --recursive
        is_recursive = re.search(r'(?:\s|^)-[a-zA-Z]*[rR][a-zA-Z]*\b|(?:\s|^)--recursive\b', cmd)
        # Check for force option: -f or --force (must not be part of --force-with-lease/etc)
        is_force = re.search(r'(?:\s|^)-[a-zA-Z]*[fF][a-zA-Z]*\b|(?:\s|^)--force(?!-)\b', cmd)
        if is_recursive and is_force:
            return True, "Destructive command blocked: recursive force deletion (`rm -rf`)."

    # 2. DROP TABLE / DROP DATABASE
    if re.search(r'\bDROP\s+(?:TABLE|DATABASE)\b', cmd, re.IGNORECASE):
        return True, "Destructive database operation blocked: `DROP TABLE` or `DROP DATABASE`."

    # 3. git push --force / git push -f
    if re.search(r'\bgit\s+push\b', cmd):
        if re.search(r'(?:\s|^)(?:--force(?!-)|-f)\b', cmd):
            return True, "Dangerous action blocked: force push (`git push --force`). Use `git push --force-with-lease`."

    # 4. TRUNCATE
    if re.search(r'\bTRUNCATE\b', cmd, re.IGNORECASE):
        return True, "Destructive database operation blocked: `TRUNCATE`."

    # 5. DELETE FROM without WHERE
    if re.search(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', cmd, re.IGNORECASE):
            return True, "Dangerous SQL command blocked: `DELETE FROM` without a `WHERE` clause."

    return False, ""

def log_blocked(cmd: str, reason: str):
    """Logs blocked commands to ~/.claude/hooks/blocked.log with metadata."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        project_path = os.getcwd()
        log_entry = {
            "timestamp": timestamp,
            "command": cmd,
            "project_path": project_path,
            "reason": reason
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Silent fail on logging errors

def main():
    try:
        # Read JSON context from stdin
        stdin_content = sys.stdin.read()
        if not stdin_content.strip():
            sys.exit(0)
            
        payload = json.loads(stdin_content)
    except Exception:
        # If payload is malformed or not JSON, allow to avoid breaking tool execution
        sys.exit(0)

    # Resolve command from input payload
    cmd = find_command(payload)
    if not cmd or not isinstance(cmd, str):
        sys.exit(0)

    blocked, reason = check_destructive(cmd)
    if blocked:
        # Log the blocked attempt
        log_blocked(cmd, reason)
        
        # Display clear error message to Claude via stderr
        sys.stderr.write(f"🛑 [BLOCKED BY HOOK] {reason}\n")
        
        # Output hookSpecificOutput for official integration
        output_data = {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }
        print(json.dumps(output_data))
        
        # Exit with block code 2
        sys.exit(2)

    # Allow normal execution
    sys.exit(0)

if __name__ == "__main__":
    main()
