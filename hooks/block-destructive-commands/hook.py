#!/usr/bin/env python3
"""
Pre-tool-use hook: blocks destructive bash commands before they run.
Install: copy to ~/.claude/hooks/block-destructive-commands.py
"""

import json
import sys
import os
import re
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

PATTERNS = [
    (r'\brm\s+-[^\s]*r[^\s]*\s*[/-]', "rm with recursive flag on root/system path"),
    (r'\brm\s+-rf\b', "rm -rf (recursive force delete)"),
    (r'\brm\s+-fr\b', "rm -fr (recursive force delete)"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE (destroys database table and all data)"),
    (r'\bDROP\s+DATABASE\b', "DROP DATABASE (destroys entire database)"),
    (r'\bTRUNCATE\b', "TRUNCATE (wipes all rows from table)"),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "DELETE FROM without WHERE (deletes all rows)"),
    (r'\bgit\s+push\s+.*--force\b', "git push --force (overwrites remote history)"),
    (r'\bgit\s+push\s+.*-f\b', "git push -f (overwrites remote history)"),
    (r'\bgit\s+reset\s+--hard\b', "git reset --hard (discards all uncommitted changes)"),
    (r'\bchmod\s+-R\s+777\b', "chmod -R 777 (insecure recursive permission change)"),
    (r'>\s*/dev/sd[a-z]', "writing directly to a block device"),
    (r'\bdd\s+.*of=/dev/sd', "dd to block device (can wipe disk)"),
    (r'\bmkfs\b', "mkfs (formats/wipes filesystem)"),
    (r'\bshred\b', "shred (irreversible file destruction)"),
]

def log_blocked(command: str, reason: str, project_path: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED | project={project_path} | reason={reason} | cmd={command}\n")

def check_command(command: str) -> tuple[bool, str]:
    for pattern, reason in PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = payload.get("cwd") or os.getcwd()

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, reason, project_path)
        result = {
            "decision": "block",
            "reason": (
                f"🚫 Blocked: {reason}\n\n"
                f"Command: {command}\n\n"
                "This command was blocked because it could cause irreversible data loss. "
                "If you're sure you want to run it, execute it manually in your terminal. "
                f"Blocked attempts are logged to {LOG_FILE}"
            )
        }
        print(json.dumps(result))
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
