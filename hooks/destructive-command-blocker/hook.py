#!/usr/bin/env python3
"""
Destructive Command Blocker — Claude Code pre-tool-use hook
============================================================

Intercepts dangerous bash commands before execution and blocks them.
Designed for ~/.claude/hooks/ as a pre-tool-use hook.

Blocked patterns:
  - rm -rf (recursive force delete)
  - DROP TABLE / DROP DATABASE
  - git push --force / git push -f
  - TRUNCATE TABLE
  - DELETE FROM without WHERE clause
  - chmod 777 (world-writable permissions)
  - mkfs (filesystem format)
  - dd if= (raw disk write)
  - > /dev/sda (direct disk overwrite)

Usage:
  As Claude Code hook: Add to ~/.claude/hooks/pre-tool-use
  Standalone test: echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | python3 hook.py
"""

import json
import sys
import os
import re
from datetime import datetime, timezone

# --- Configuration ---
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
BLOCKED_EXIT_CODE = 2  # Non-zero = block the tool call

# --- Destructive patterns ---
# Each pattern: (compiled regex, human-readable description)
BLOCKED_PATTERNS = [
    # File destruction
    (re.compile(r'\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f|rm\s+.*-[a-zA-Z]*f[a-zA-Z]*r|\brm\s+-rf\b|\brm\s+-fr\b', re.IGNORECASE),
     "Recursive force delete (rm -rf)"),
    
    # SQL destruction
    (re.compile(r'\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b', re.IGNORECASE),
     "SQL DROP statement"),
    (re.compile(r'\bTRUNCATE\s+(TABLE\s+)?\w+', re.IGNORECASE),
     "SQL TRUNCATE statement"),
    (re.compile(r'\bDELETE\s+FROM\s+\w+\s*(?:;|\s*$)(?!.*\bWHERE\b)', re.IGNORECASE | re.DOTALL),
     "DELETE FROM without WHERE clause"),
    
    # Git force push
    (re.compile(r'\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b', re.IGNORECASE),
     "Git force push (rewrites remote history)"),
    
    # System destruction
    (re.compile(r'\bchmod\s+777\b'),
     "World-writable permissions (chmod 777)"),
    (re.compile(r'\bmkfs\b'),
     "Filesystem format (mkfs)"),
    (re.compile(r'\bdd\s+if=', re.IGNORECASE),
     "Raw disk write (dd)"),
    (re.compile(r'>\s*/dev/[sh]d[a-z]'),
     "Direct disk device overwrite"),
    
    # Container/system escape
    (re.compile(r'\b(curl|wget)\s+.*\|\s*(sudo\s+)?(ba)?sh\b', re.IGNORECASE),
     "Piping remote content to shell"),
]

# --- Additional DELETE FROM check (needs special handling) ---
def is_delete_without_where(command: str) -> bool:
    """Check for DELETE FROM without a WHERE clause."""
    # Find all DELETE FROM statements
    delete_pattern = re.compile(r'\bDELETE\s+FROM\s+\w+', re.IGNORECASE)
    where_pattern = re.compile(r'\bWHERE\b', re.IGNORECASE)
    
    matches = list(delete_pattern.finditer(command))
    if not matches:
        return False
    
    for match in matches:
        # Check if there's a WHERE after this DELETE
        remainder = command[match.end():]
        # Look for WHERE before the next semicolon or end of string
        semicolon_pos = remainder.find(';')
        if semicolon_pos >= 0:
            segment = remainder[:semicolon_pos]
        else:
            segment = remainder
        
        if not where_pattern.search(segment):
            return True
    
    return False


def check_command(command: str) -> tuple[bool, str]:
    """
    Check a command against blocked patterns.
    Returns (is_blocked, reason).
    """
    for pattern, description in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, description
    
    # Special check for DELETE without WHERE
    if is_delete_without_where(command):
        return True, "DELETE FROM without WHERE clause"
    
    return False, ""


def log_blocked(command: str, reason: str, project_path: str):
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = (
        f"[{timestamp}] BLOCKED: {reason}\n"
        f"  Command: {command[:500]}\n"
        f"  Project: {project_path}\n"
        f"---\n"
    )
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def main():
    """
    Read hook input from stdin, check for destructive commands.
    Exit 0 to allow, non-zero to block.
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)  # No input = allow
        
        hook_input = json.loads(raw)
    except (json.JSONDecodeError, KeyError):
        # If we can't parse input, allow (fail-open for non-bash tools)
        sys.exit(0)
    
    # Only check bash/shell tool calls
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("bash", "shell", "terminal", "execute", "exec"):
        sys.exit(0)  # Not a bash command, allow
    
    # Extract the command
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "") or tool_input.get("cmd", "") or ""
    
    if not command:
        sys.exit(0)
    
    # Check against patterns
    is_blocked, reason = check_command(command)
    
    if is_blocked:
        project_path = hook_input.get("project_path", os.getcwd())
        log_blocked(command, reason, project_path)
        
        # Output message for Claude to see
        error_msg = {
            "error": f"BLOCKED: {reason}",
            "message": (
                f"This command was blocked by the destructive command safety hook. "
                f"Reason: {reason}. "
                f"If this command is intentional, please modify it to be safer "
                f"(e.g., use specific paths instead of recursive force delete, "
                f"add a WHERE clause to DELETE statements, or avoid force-pushing)."
            ),
            "blocked_command": command[:200],
        }
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(BLOCKED_EXIT_CODE)
    
    # Command is safe, allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
