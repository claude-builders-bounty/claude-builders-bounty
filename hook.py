#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.
Place in ~/.claude/hooks/ and configure in settings.json
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Log file location
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Dangerous command patterns
BLOCKED_PATTERNS = [
    # rm -rf variations
    (r"rm\s+-rf\s+/\s*$", "rm -rf / (root filesystem deletion)"),
    (r"rm\s+-rf\s+\*\s*$", "rm -rf * (all files in current directory)"),
    (r"rm\s+-rf\s+~", "rm -rf ~ (home directory deletion)"),
    (r"rm\s+-rf\s+\.\.", "rm -rf .. (parent directory deletion)"),
    # SQL destructive commands
    (r"DROP\s+TABLE", "DROP TABLE"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE"),
    (r"DELETE\s+FROM\s+\w+\s*;", "DELETE FROM without WHERE clause"),
    (r"DELETE\s+FROM\s+\w+\s*$", "DELETE FROM without WHERE clause"),
    # Git destructive commands
    (r"git\s+push\s+--force", "git push --force"),
    (r"git\s+push\s+origin\s+.*--force", "git push origin --force"),
    # System destructive
    (r":()\s*{\s*:\|:&\s*}`, `", "fork bomb"),
    (r"mkfs\.", "filesystem format"),
    (r"dd\s+if=/dev/zero", "dd disk wipe"),
    (r">\s*/dev/sda", "direct disk write"),
    (r"chmod\s+-R\s+777\s+/", "chmod recursive on root"),
]

def log_blocked(command: str, cwd: str):
    """Log blocked command to blocked.log"""
    timestamp = datetime.now().isoformat()
    log_entry = f'{timestamp} command="{command}" path="{cwd}"\n'
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract tool info (Claude Code hook format)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only check bash commands
        if tool_name != "bash":
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)
        
        command = tool_input.get("command", "")
        cwd = os.getcwd()
        
        # Check against blocked patterns
        for pattern, description in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                log_blocked(command, cwd)
                print(json.dumps({
                    "decision": "block",
                    "reason": f"Blocked dangerous command: {description}",
                    "message": f"🛑 Blocked: {description}\nThis command could cause irreversible data loss. If you meant to run this, please review the command carefully or use a safer alternative."
                }))
                sys.exit(0)
        
        # Allow the command
        print(json.dumps({"decision": "allow"}))
        
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # On error, allow (fail open for usability)
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()