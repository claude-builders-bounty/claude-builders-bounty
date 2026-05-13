#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Commands

Installation:
  1. Place this file in ~/.claude/hooks/block-destructive.py
  2. Make it executable: chmod +x ~/.claude/hooks/block-destructive.py

This hook intercepts dangerous bash commands and prevents their execution.
"""

import os
import sys
import re
import json
import stat
from datetime import datetime, timezone

HOOK_LOG = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "blocked.log")

# Patterns that are blocked
BLOCK_PATTERNS = [
    (r"rm\s+-rf\s+", "Recursive force delete"),
    (r"DROP\s+TABLE", "DROP TABLE without confirmation"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE"),
    (r"git\s+push\s+--\s*force", "Force push to remote"),
    (r"git\s+push\s+-f\b", "Force push (-f flag)"),
    (r"git\s+push\s+--force-with-lease", "Force push with lease (destructive)"),
    (r"shred\s+", "Secure file deletion"),
    (r"dd\s+.*of=/", "Direct disk write (dd)"),
    (r"cat\s+/dev/zero", "Writing zeros to disk"),
    # DELETE FROM without WHERE clause
    (r"DELETE\s+FROM\s+[^\s;]+\s*;", "DELETE FROM without WHERE clause"),
]

# For commands with WHERE, flag suspicious ones
SUSPICIOUS_WHERE = [
    (r"DELETE\s+FROM\s+[^\s;]+WHERE\s+1\s*=\s*1", "DELETE with always-true WHERE (1=1)"),
    (r"DELETE\s+FROM\s+[^\s;]+WHERE\s+\w+\s*=\s*['\"]?['\"]?\s*(;|$)", "DELETE with empty/null condition"),
]


def log_blocked(command, reason, project_path):
    """Log a blocked command attempt."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = f"[{timestamp}] BLOCKED: {reason}\n  Command: {command}\n  Project: {project_path}\n"
    try:
        os.makedirs(os.path.dirname(HOOK_LOG), exist_ok=True)
        with open(HOOK_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[block-destructive] WARNING: Could not write to log: {e}", file=sys.stderr)


def is_destructive(command):
    """Check if a command should be blocked."""
    cmd = command.strip()
    
    # Check exact block patterns
    for pattern, reason in BLOCK_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return reason
    
    # Check suspicious WHERE patterns
    for pattern, reason in SUSPICIOUS_WHERE:
        if re.search(pattern, cmd, re.IGNORECASE):
            return reason
    
    return None


def main():
    # Claude Code passes hook data via stdin as JSON
    try:
        hook_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        # Not valid JSON, let it pass through
        sys.exit(0)
    
    tool_name = hook_data.get("tool", "unknown")
    tool_input = hook_data.get("input", {})
    
    # Only intercept bash commands
    if tool_name != "Bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    # Get project path from env
    project_path = os.environ.get("CLAUDE_PROJECT_PATH", os.getcwd())
    
    reason = is_destructive(command)
    
    if reason:
        log_blocked(command, reason, project_path)
        
        # Print block message to stderr (visible in Claude Code output)
        block_msg = (
            f"\n"
            f"========================================\n"
            f"  HOOK BLOCKED: {reason}\n"
            f"========================================\n"
            f"  Command: {command}\n"
            f"  Reason: {reason}\n"
            f"\n"
            f"  This command was blocked by the pre-tool-use hook.\n"
            f"  If you need to proceed, you can:\n"
            f"  1. Use a safer alternative (e.g., `rm -i` instead of `rm -rf`)\n"
            f"  2. Add a WHERE clause to DELETE statements\n"
            f"  3. Use `--force` with caution on non-production environments\n"
            f"\n"
            f"  Blocked attempts are logged to: {HOOK_LOG}\n"
            f"========================================\n"
        )
        print(block_msg, file=sys.stderr)
        
        # Exit with error to block the command
        sys.exit(1)
    
    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()