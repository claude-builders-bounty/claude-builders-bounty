#!/usr/bin/env python3
"""
claude-security-hook — Claude Code PreToolUse hook that blocks destructive
bash commands from executing. Drops into ~/.claude/hooks/pre_tool_use/ as
a Claude Code hook.

Install:
  mkdir -p ~/.claude/hooks/pre_tool_use
  cp guard.py ~/.claude/hooks/pre_tool_use/
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_NAME = "claude-security-hook"

# ── Dangerous Patterns ────────────────────────────────────────────────

# Each rule: (pattern, reason, severity)
DANGEROUS_PATTERNS = [
    # File destruction
    (r'\brm\s+(-rf?|--recursive|--force|-fr)\s', 'Destructive file removal (rm -rf)'),
    (r'\brm\s+(-rf?|--recursive|--force)', 'Forceful file removal'),
    (r'\brm\b.*\s+/\s', 'Attempting to remove root directory'),
    
    # git destructive
    (r'\bgit\s+push\s+(-f|--force)\b', 'Force push (git push --force) — can overwrite remote history'),
    (r'\bgit\s+branch\s+-D\b', 'Force delete a git branch'),
    (r'\bgit\s+reset\s+--hard\b', 'Hard git reset — can lose uncommitted changes'),
    
    # Database destruction (SQL)
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|PROCEDURE|FUNCTION)\b',
     'DROP statement — permanent deletion of database objects'),
    (r'\bTRUNCATE\b', 'TRUNCATE table — irreversible data removal'),
    (r'\bDELETE\s+FROM\b(?!\s+.*\bWHERE\b)', 
     'DELETE FROM without WHERE clause — would delete all rows'),
    (r'\bALTER\s+TABLE\b.*\bDROP\b', 'ALTER TABLE DROP — could delete columns or constraints'),
    
    # System dangerous
    (r'(^|\||;|&&)\s*(mkfs|dd\s+if=|format|fdisk|parted)\b',
     'Dangerous disk/filesystem operation'),
    (r'(^|\||;|&&)\s*chmod\s+-?R?\s*0{1,4}\s', 'chmod to 0 — removes all permissions'),
    (r'(^|\||;|&&)\s*chown\s+-R\b', 'Recursive chown (use with caution)'),
    
    # Network dangerous
    (r'\bwget\s+.*\|?\s*bash\b', 'Pipe wget to bash — remote code execution risk'),
    (r'\bcurl\s+.*\|?\s*bash\b', 'Pipe curl to bash — remote code execution risk'),
]

# Patterns that should NEVER be blocked (allowlist)
ALLOWLIST = [
    r'rm\s+-rf\s+/tmp/',
    r'rm\s+-rf\s+\~?/\.?(cache|npm|yarn|pip)/',
    r'rm\s+-rf\s+node_modules',
    r'rm\s+-rf\s+\.?next',
    r'rm\s+-rf\s+dist',
    r'rm\s+-rf\s+build',
    r'rm\s+-rf\s+__pycache__',
    r'rm\s+-rf\s+\.?venv',
    r'rm\s+-rf\s+\.?tox',
    r'git\s+reset\s+--hard\s+HEAD',
    r'git\s+push\s+--force-with-lease',
    r'git\s+push\s+-f\s+origin\s+HEAD:',  # pushing current branch
]


def is_allowed(command: str) -> bool:
    """Check if command matches any allowlist pattern."""
    for pattern in ALLOWLIST:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def check_command(command: str, project_path: str = "") -> dict | None:
    """
    Check a command against dangerous patterns.
    Returns a dict with block info if dangerous, None otherwise.
    """
    if is_allowed(command):
        return None

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "blocked": True,
                "command": command,
                "reason": reason,
                "pattern": pattern,
                "project_path": project_path or os.getcwd(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hook": HOOK_NAME,
            }
    return None


def log_blocked(block_info: dict):
    """Log a blocked command to the log file."""
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    
    log_entry = (
        f"[{block_info['timestamp']}] "
        f"BLOCKED | {block_info['reason']} | "
        f"cmd: {block_info['command'][:200]} | "
        f"project: {block_info['project_path']}\n"
    )
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def format_block_message(block_info: dict) -> str:
    """Format a clear message explaining why the command was blocked."""
    return (
        f"⛔ **Command Blocked by {HOOK_NAME}**\n\n"
        f"**Reason:** {block_info['reason']}\n"
        f"**Command:** `{block_info['command'][:200]}`\n\n"
        f"This command could be destructive. If you're sure you want to run it:\n"
        f"1. Review the command carefully\n"
        f"2. Break it into safer individual steps\n"
        f"3. Or add an exception to your hook configuration\n\n"
        f"*Block logged to ~/.claude/hooks/blocked.log*"
    )


def main():
    """
    Entry point for Claude Code hook system.
    Claude Code passes the tool use as JSON on stdin.
    
    Expected input format (Claude Code hook protocol):
    {
      "tool": "Bash",
      "args": {"command": "...", ...},
      "project_path": "..."
    }
    """
    # Read input from Claude Code
    try:
        raw = sys.stdin.read()
        if not raw:
            return  # No input, nothing to check
        
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Not JSON — may be a direct command string from testing
        payload = {"args": {"command": raw.strip()}}
    except Exception as e:
        # Unknown format, don't block
        return

    # Extract command
    args = payload.get("args", {})
    command = args.get("command", "") or ""
    project_path = payload.get("project_path", args.get("workdir", ""))

    if not command.strip():
        return  # Empty command, allow

    # Check the command
    result = check_command(command, project_path)
    if result is None:
        return  # Command is safe, allow execution

    # Log and block
    log_blocked(result)
    block_msg = format_block_message(result)
    
    # Output block result as JSON for Claude Code
    output = {
        "result": {
            "status": "error",
            "message": block_msg,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
