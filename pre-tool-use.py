import sys
import json
import os
import re
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            pwd = os.getcwd()
            f.write(f"[{timestamp}] Blocked: {command} | Path: {pwd}\n")
    except Exception:
        pass

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # If it's not valid JSON, just pass

    tool_name = data.get("tool_name")
    
    # We only care about bash commands
    if tool_name not in ["Bash", "bash"]:
        sys.exit(0)
        
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check for destructive patterns
    destructive_patterns = [
        r"rm\s+-r?f",                # rm -rf, rm -f
        r"DROP\s+TABLE",             # DROP TABLE
        r"git\s+push\s+.*--force",   # git push --force
        r"TRUNCATE",                 # TRUNCATE
    ]
    
    # Special check for DELETE FROM without WHERE
    # It checks if DELETE FROM is present but WHERE is not after it
    # We'll use a simple approach: if "DELETE FROM" is in the command and "WHERE" is not in the command
    
    is_destructive = False
    
    for pattern in destructive_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            is_destructive = True
            break
            
    if re.search(r"DELETE\s+FROM", command, re.IGNORECASE) and not re.search(r"WHERE", command, re.IGNORECASE):
        is_destructive = True
        
    if is_destructive:
        log_blocked(command)
        print("Security block: This command contains destructive patterns (e.g. rm -rf, DROP TABLE, git push --force, TRUNCATE, or DELETE FROM without WHERE) and is not allowed by the safety hook.", file=sys.stderr)
        sys.exit(2)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
