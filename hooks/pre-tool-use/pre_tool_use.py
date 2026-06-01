#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Install: symlink to ~/.claude/hooks/pre_tool_use.py

Blocked patterns:
  - rm -rf (recursive force delete)
  - DROP TABLE / DROP DATABASE
  - git push --force / --force-with-lease
  - TRUNCATE TABLE
  - DELETE FROM without WHERE clause
  - chmod 777
  - :(){ :|:& };: (fork bomb)

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")
os.makedirs(LOG_DIR, exist_ok=True)

# Patterns: (regex, human-readable reason)
BLOCKED_PATTERNS = [
    (r"rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b", "recursive force delete (rm -rf)"),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "DROP TABLE/DATABASE/SCHEMA statement"),
    (r"git\s+push\s+.*(--force|--force-with-lease|--delete)\b", "force push to remote"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE TABLE statement"),
    (r"\bDELETE\s+FROM\s+\w+\s*$", "DELETE FROM without WHERE clause"),
    (r"\bDELETE\s+FROM\s+\w+(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause"),
    (r"chmod\s+(-R\s+)?777\b", "world-writable permissions (chmod 777)"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "fork bomb detected"),
    (r">\s*/dev/sda", "direct write to block device"),
    (r"mkfs\.\w+", "filesystem format command"),
    (r"dd\s+if=.*\s+of=/dev/\w+", "dd to block device"),
    (r"\bDROP\s+INDEX\b", "DROP INDEX statement"),
]

def log_blocked(command, reason, project_path=""):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = json.dumps({
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "project": project_path,
    })
    print(entry, file=sys.stderr)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only intercept bash/terminal commands
    if tool_name not in ("bash", "terminal", "Bash", "execute_command"):
        print(json.dumps({"continue": True}))
        return
    
    command = tool_input.get("command", "") or tool_input.get("input", "") or ""
    
    if not command:
        print(json.dumps({"continue": True}))
        return
    
    # Remove leading/trailing whitespace and newlines
    command = command.strip()
    
    # Get project path from environment if available
    project_path = os.getenv("CLAUDE_PROJECT_DIR", os.getcwd())
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason, project_path)
            result = {
                "continue": False,
                "reason": f"Blocked: {reason}",
                "message": f"""
🚫 COMMAND BLOCKED

The following command was intercepted by the safety hook:

  {command}

Reason: This matches the blocked pattern `{pattern}` ({reason}).
This operation could cause irreversible damage.

If you're ABSOLUTELY certain this is safe:
  1. Review the command carefully
  2. Run it manually in the terminal
  3. Consider adding a safer alternative (e.g., `rm -i` instead of `rm -rf`)
""".strip(),
            }
            print(json.dumps(result))
            return
    
    # Safe — allow
    print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
