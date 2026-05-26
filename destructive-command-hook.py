#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands before execution.
Install: Place this script in ~/.claude/hooks/ and configure hooks.json
"""

import json
import sys
import os
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    # File system destruction
    (r"\brm\s+-rf\b", "rm -rf (recursive force delete)"),
    (r"\brm\s+.*--no-preserve-root\b", "rm --no-preserve-root"),
    
    # Database destruction
    (r"\bDROP\s+TABLE\b", "DROP TABLE statement"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE statement"),
    (r"\bTRUNCATE\b", "TRUNCATE statement (removes all rows without backup)"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause"),
    
    # Git force push
    (r"\bgit\s+push\s+.*--force\b", "git push --force (overwrites remote history)"),
    (r"\bgit\s+push\s+.*-f\b", "git push -f (force push)"),
    (r"\bgit\s+push\s+.*--delete\b", "git push --delete (deletes remote branch)"),
    
    # Sensitive file operations
    (r"\bchmod\s+777\b", "chmod 777 (world-writable permissions)"),
    (r"\bdd\s+if=", "dd command (direct disk write)"),
    (r"\b>(\s*)/dev/sd", "Writing directly to disk device"),
    
    # System-level dangerous
    (r"\breboot\b", "system reboot"),
    (r"\bshutdown\b", "system shutdown"),
    (r"\bkill\s+-9\b", "kill -9 (forced process termination)"),
]

import re

def log_blocked(command: str, project_path: str):
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Project: {project_path}\n"
        f"  Command: {command}\n"
        f"{'─' * 60}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def check_command(command: str) -> tuple[bool, str]:
    """Check if a command matches any dangerous pattern.
    Returns (is_dangerous, reason)."""
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""

def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"decision": "allow"}))
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("cwd", os.getcwd())
    
    # Only check bash/terminal commands
    if tool_name not in ("bash", "terminal", "execute_command"):
        print(json.dumps({"decision": "allow"}))
        return 0

    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
    
    if not command:
        print(json.dumps({"decision": "allow"}))
        return 0

    is_dangerous, reason = check_command(command)
    
    if is_dangerous:
        log_blocked(command, project_path)
        message = (
            f"🚫 BLOCKED: This command matches dangerous pattern: {reason}\n"
            f"Command: {command}\n"
            f"Log saved to: {LOG_FILE}\n"
            f"Please explain why this command is necessary, or use a safer alternative."
        )
        result = {
            "decision": "block",
            "message": message
        }
    else:
        result = {"decision": "allow"}

    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
