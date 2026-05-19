#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.
Installs to ~/.claude/hooks/pre-tool-use.json

Usage: Just run `pip install -r requirements.txt` and copy config.
See README.md for full instructions.
"""

import json
import sys
import os
from datetime import datetime

# Destructive patterns to block
DESTRUCTIVE_PATTERNS = [
    # File system destruction
    (r'\brm\s+-rf\b', "rm -rf: Recursive force delete — use trash or confirm target explicitly"),
    (r'\brm\s+.*-f\b(?!\s*--preserve-root)', "rm -f: Force delete without confirmation"),
    (r'\bchmod\s+777\b', "chmod 777: Overly permissive — use minimum required permissions"),
    (r'\bdd\s+.*of=/dev/', "dd to /dev/: Direct disk write — extremely dangerous"),
    (r'\bmkfs\b', "mkfs: Format filesystem — destroys all data on target"),
    (r'\bshred\b', "shred: Secure file deletion — irreversible"),

    # Database destruction
    (r'\bDROP\s+TABLE\b', "DROP TABLE: Destroys table and all data"),
    (r'\bDROP\s+DATABASE\b', "DROP DATABASE: Destroys entire database"),
    (r'\bTRUNCATE\s+', "TRUNCATE: Removes all rows from table"),
    (r'\bDELETE\s+FROM\b(?!\s*.*\bWHERE\b)', "DELETE FROM without WHERE: Deletes ALL rows — add a WHERE clause"),

    # Git destruction
    (r'\bgit\s+push\s+.*--force\b', "git push --force: Rewrites remote history — use --force-with-lease"),
    (r'\bgit\s+push\s+-f\b', "git push -f: Force push detected"),
    (r'\bgit\s+reset\s+--hard\b', "git reset --hard: Discards all uncommitted changes"),
    (r'\bgit\s+clean\s+-fd\b', "git clean -fd: Removes untracked files and directories"),
    (r'\bgit\s+branch\s+-D\b', "git branch -D: Force deletes branch without merge check"),

    # System destruction
    (r'\bkill\s+-9\s+1\b', "kill -9 1: Attempting to kill init process"),
    (r'\bsudo\s+rm\s+-rf\s+/', "sudo rm -rf /: System destruction"),
    (r'\b>\s*/dev/sd', "Direct write to block device — destroys partition"),
    (r'\bmv\s+/.*\s+/', "mv to /: Moving to root — likely accidental"),
]

# Patterns that are explicitly allowed (whitelist overrides)
ALLOWED_PATTERNS = [
    r'rm\s+-rf\s+.*\.git/objects',  # Git gc is fine
    r'#\s*unsafe.*allow',  # Explicit override comment
    r'echo.*#.*dangerous',  # Example/demonstration commands
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def check_allowed(command):
    """Check if command matches any whitelist pattern."""
    import re
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def check_destructive(command):
    """Check if command matches any destructive pattern. Returns reason or None."""
    import re
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return None

def log_blocked(command, reason, project_path):
    """Log blocked attempt to file."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command.strip(),
            "reason": reason,
            "project_path": project_path
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Never fail on logging

def main():
    # Read hook input from stdin
    hook_input = json.load(sys.stdin)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Bash commands
    if tool_name != "Bash":
        # Allow all non-bash tools
        print(json.dumps({"decision": "allow"}))
        return

    command = tool_input.get("command", "")
    project_path = os.getcwd()

    # Check whitelist first
    if check_allowed(command):
        print(json.dumps({"decision": "allow"}))
        return

    # Check destructive patterns
    reason = check_destructive(command)
    if reason:
        # Log the blocked attempt
        log_blocked(command, reason, project_path)

        # Block with clear explanation
        print(json.dumps({
            "decision": "block",
            "reason": f"🚫 BLOCKED: {reason}\n\n"
                      f"Command: {command.strip()}\n\n"
                      f"If this is intentional, add '# unsafe: allow' to the command."
        }))
        return

    # Allow safe commands
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
