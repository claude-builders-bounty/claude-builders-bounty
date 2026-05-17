#!/usr/bin/env python3
"""
pre-tool-use-hook.py — Claude Code pre-tool-use hook
Blocks dangerous bash commands before execution.
Place in ~/.claude/hooks/ and configure in claude_settings.json
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))

# Patterns that match dangerous commands (case-insensitive)
DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf (recursive force remove)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE (deletes entire database table)'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE (deletes entire database)'),
    (r'\bgit\s+push\s+.*--force', 'git push --force (overwrites remote history)'),
    (r'\bgit\s+push\s+.*-f\b', 'git push -f (overwrites remote history)'),
    (r'\bTRUNCATE\s+(TABLE\s+)?', 'TRUNCATE (deletes all rows from table)'),
    (r'\bDELETE\s+FROM\s+(?!.*\bWHERE\b)', 'DELETE FROM without WHERE (deletes all rows)'),
    (r'\bchmod\s+777\b', 'chmod 777 (world-writable permissions)'),
    (r'\b:\s*\{\s*:\|:&\s*\};:', 'Fork bomb pattern'),
    (r'>\s*/dev/sda', 'Writing directly to disk device'),
]

def log_blocked(command, project_path):
    """Log blocked attempt with timestamp."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = f"[{timestamp}] BLOCKED | project={project_path} | command={command}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(entry)

def check_command(command, project_path):
    """Check if command matches any dangerous pattern."""
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, project_path)
            return False, description
    return True, None

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}), flush=True)
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("cwd", os.getcwd())

    # Only intercept bash/terminal commands
    if tool_name not in ("bash", "terminal", "RunShellCommand", "execute_command"):
        print(json.dumps({"continue": True}), flush=True)
        return

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"continue": True}), flush=True)
        return

    allowed, reason = check_command(command, project_path)

    if not allowed:
        response = {
            "continue": False,
            "reason": (
                f"⚠️  BLOCKED: Dangerous command detected ({reason})\n\n"
                f"Command: {command}\n"
                f"This command could cause irreversible damage. "
                f"It has been logged to {LOG_FILE}.\n\n"
                f"If you are absolutely certain this is safe, "
                f"review and modify the hook at {__file__}"
            )
        }
        print(json.dumps(response), flush=True)
    else:
        print(json.dumps({"continue": True}), flush=True)

if __name__ == "__main__":
    main()
