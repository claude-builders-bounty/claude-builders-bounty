#!/usr/bin/env bash
# Read full stdin JSON from Claude Code
STDIN_DATA=$(cat)

# Run Python validator inline
python3 -c '
import sys
import json
import re
from datetime import datetime
import os

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command, project_path):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.now().isoformat()
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] Command: {command} | Project: {project_path}\n")
    except Exception:
        pass

def is_destructive(cmd):
    cmd_clean = cmd.strip()
    # 1. rm -rf / fr
    if re.search(r"\brm\s+-[a-zA-Z]*rf\b", cmd_clean) or re.search(r"\brm\s+-[a-zA-Z]*fr\b", cmd_clean):
        return "rm -rf (recursive force delete)"
    # 2. DROP TABLE
    if re.search(r"\bDROP\s+TABLE\b", cmd_clean, re.IGNORECASE):
        return "DROP TABLE statement"
    # 3. git push --force / -f
    if re.search(r"\bgit\s+push\s+.*(--force|-f)\b", cmd_clean) or re.search(r"\bgit\s+push\s+.*-f\s+", cmd_clean) or cmd_clean.endswith(" -f"):
        if "--dry-run" not in cmd_clean and "--help" not in cmd_clean:
            return "git push --force"
    # 4. TRUNCATE
    if re.search(r"\bTRUNCATE\b", cmd_clean, re.IGNORECASE):
        return "TRUNCATE statement"
    # 5. DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", cmd_clean, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", cmd_clean, re.IGNORECASE):
            return "DELETE FROM without a WHERE clause"
    return None

try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)

tool_name = data.get("tool_name", "")
tool_input = data.get("tool_input", {})

if str(tool_name).lower() in ["bash", "execute_command", "run_command", "execute_bash"]:
    cmd = tool_input.get("command", "")
    reason = is_destructive(cmd)
    if reason:
        project_path = os.getcwd()
        log_blocked(cmd, project_path)
        response = {
            "decision": "block",
            "reason": f"Command blocked by safety hook: Destructive pattern \"{reason}\" detected."
        }
        print(json.dumps(response))
        sys.exit(2)
sys.exit(0)
' "$STDIN_DATA"
