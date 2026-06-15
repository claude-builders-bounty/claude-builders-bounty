#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Installation:
    mkdir -p ~/.claude/hooks && cp blocker.py ~/.claude/hooks/pre-tool-use/

Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import re
import sys
import json
from datetime import datetime
from pathlib import Path

# Destructive patterns (triggers block)
DESTRUCTIVE_PATTERNS = [
    # rm -rf / or rm -rf * (dangerous)
    (r'rm\s+-rf\s+[/*]', 'rm -rf on root or wildcard'),
    (r'rm\s+-rf\s+/(?!\S)', 'rm -rf on root directory'),
    
    # SQL without safety
    (r'DROP\s+TABLE\s+(?!IF\s+EXISTS)', 'DROP TABLE without IF EXISTS'),
    (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE'),
    (r'DELETE\s+FROM\s+\w+\s*$', 'DELETE without WHERE clause'),
    
    # Git force push (not --force-with-lease)
    (r'git\s+push.*--force(?!-with-lease)', 'git push --force without --force-with-lease'),
    (r'git\s+push.*-f(?!.*--force-with-lease)', 'git push -f without --force-with-lease'),
    
    # Dangerous filesystem operations
    (r'mkfs', 'mkfs command'),
    (r'chmod\s+-R\s+000\s+/', 'chmod -R 000 on root'),
    
    # Fork bomb
    (r':\(\)\s*\{\s*:\s*\|', 'fork bomb pattern'),
]

# Safe overrides (explicitly allowed)
SAFE_OVERRIDES = [
    # Relative paths (safe)
    (r'rm\s+-rf\s+\./', 'relative path rm'),
    (r'rm\s+-rf\s+\.\./', 'relative path rm'),
    
    # DROP TABLE IF EXISTS (migration-safe)
    (r'DROP\s+TABLE\s+IF\s+EXISTS', 'DROP TABLE IF EXISTS'),
    
    # DELETE with WHERE (scoped)
    (r'DELETE\s+FROM\s+.+?\s+WHERE\s+', 'DELETE with WHERE clause'),
    
    # git push --force-with-lease (safer)
    (r'git\s+push.*--force-with-lease', 'git push --force-with-lease'),
]


def is_destructive(command: str) -> tuple:
    """
    Check if a command is destructive.
    Returns (is_destructive, reason).
    """
    # Check safe overrides first
    for pattern, desc in SAFE_OVERRIDES:
        if re.search(pattern, command, re.IGNORECASE):
            return False, ""
    
    # Check destructive patterns
    for pattern, desc in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, desc
    
    return False, ""


def log_blocked_attempt(command: str, reason: str, project_path: str) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log"""
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "blocked.log"
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: command='{command}' reason='{reason}' project='{project_path}'\n"
    
    with open(log_file, "a") as f:
        f.write(log_entry)


def main():
    """Main hook entry point."""
    # Read JSON input from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)
    
    # Extract command from tool use
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    
    # Only check bash commands
    if tool_name != "Bash":
        # Allow non-bash tools
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    
    # Check if destructive
    is_dest, reason = is_destructive(command)
    
    if is_dest:
        # Log the blocked attempt
        project_path = data.get("cwd", "unknown")
        log_blocked_attempt(command, reason, project_path)
        
        # Return block decision with clear message
        response = {
            "decision": "deny",
            "reason": f"Destructive command blocked: {command}\nReason: {reason}\n\nIf you believe this is a false positive, use a safer alternative:\n- Use relative paths (./) for rm -rf\n- Use DROP TABLE IF EXISTS for SQL\n- Use DELETE FROM ... WHERE for scoped deletes\n- Use git push --force-with-lease instead of --force"
        }
        print(json.dumps(response))
        sys.exit(0)
    
    # Allow the command
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
