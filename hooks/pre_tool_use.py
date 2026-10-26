#!/usr/bin/env python3
"""
=============================================================================
CLAUDE CODE PRE-TOOL-USE HOOK (pre_tool_use.py)
=============================================================================
Bounty #3 Solution: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
Reward: $100 USD

Description:
  High-security gatekeeper hook that intercepts Claude Code tool calls before
  execution. Prevents catastrophic commands (rm -rf, git push --force,
  DROP TABLE/DATABASE, TRUNCATE, DELETE FROM without WHERE, fork bombs).
  Logs every violation to ~/.claude/hooks/blocked.log and returns an informative
  rejection message to Claude to prevent accidental data destruction.

Usage:
  Invoked automatically by Claude Code before tool execution, or via CLI:
    python pre_tool_use.py '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}'
=============================================================================
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Destructive pattern definitions
BLOCKED_PATTERNS = [
    # 1. Destructive filesystem removals
    (
        r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+([/~]|\*|\.\.?|/[a-zA-Z0-9_\-]+|\bC:\\|\bC:/)",
        "DANGEROUS FILE DESTRUCTION: Recursive removal on root, home, system, or wildcard directory detected."
    ),
    (
        r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+([/~]|\*|\.\.?|/[a-zA-Z0-9_\-]+|\bC:\\|\bC:/)",
        "DANGEROUS FILE DESTRUCTION: Recursive removal on root, home, system, or wildcard directory detected."
    ),
    (
        r"\brmdir\s+/[sS]\s+/[qQ]",
        "DANGEROUS WINDOWS DESTRUCTION: Silent recursive rmdir detected."
    ),
    # 2. Destructive Git commands
    (
        r"\bgit\s+push\s+.*(--force|-f)\b",
        "DESTRUCTIVE GIT COMMAND: Force-pushing can overwrite remote branch history and destroy team commits."
    ),
    (
        r"\bgit\s+reset\s+--hard\b",
        "DESTRUCTIVE GIT COMMAND: 'git reset --hard' discards uncommitted work irreversibly."
    ),
    (
        r"\bgit\s+clean\s+-[a-zA-Z]*f",
        "DESTRUCTIVE GIT COMMAND: 'git clean -f' permanently deletes untracked files without confirmation."
    ),
    # 3. Catastrophic SQL mutations
    (
        r"(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
        "DESTRUCTIVE SQL: 'DROP TABLE/DATABASE' permanently removes entire database structures."
    ),
    (
        r"(?i)\bTRUNCATE(\s+TABLE)?\b",
        "DESTRUCTIVE SQL: 'TRUNCATE' unconditionally empties tables without row recovery."
    ),
    (
        r"(?i)\bDELETE\s+FROM\s+([a-zA-Z0-9_\.\"`]+)(?!\s+WHERE\b)[^;]*;?",
        "DANGEROUS SQL: 'DELETE FROM' without a WHERE clause will wipe every row in the table."
    ),
    # 4. OS-level destructive exploits
    (
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
        "CRITICAL MALICIOUS EXPLOIT: Bash fork bomb detected."
    ),
    (
        r"\bmkfs\b",
        "CRITICAL FILESYSTEM COMMAND: 'mkfs' formats drive partitions."
    ),
    (
        r"\bdd\s+if=.*\s+of=(/dev/[a-zA-Z0-9]+|\\\\.\\)",
        "CRITICAL RAW WRITE: 'dd' raw block device overwrite detected."
    )
]

def get_blocked_log_path() -> Path:
    """Returns ~/.claude/hooks/blocked.log with fallback to local directory."""
    home = Path.home()
    log_dir = home / ".claude" / "hooks"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "blocked.log"
    except Exception:
        # Fallback to current working directory if home is read-only
        return Path.cwd() / "blocked.log"

def log_blocked_command(command: str, project_path: str, reason: str):
    """Appends to blocked.log in format: timestamp | command | project_path"""
    log_file = get_blocked_log_path()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_cmd = command.replace("\n", " ").strip()
    log_line = f"{timestamp} | {clean_cmd} | {project_path} | {reason}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        sys.stderr.write(f"[Warning] Could not write to blocked.log: {e}\n")

def check_command(command: str) -> tuple[bool, str]:
    """Inspects command against blocked regex patterns."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            # Special check for DELETE FROM: ensure there's no WHERE clause anywhere in statement
            if "DELETE" in pattern.upper() and "FROM" in pattern.upper():
                upper_cmd = command.upper()
                if "WHERE" in upper_cmd:
                    continue  # Has a WHERE clause, allow safe conditional deletion
            return True, reason
    return False, ""

def main():
    # 1. Parse payload from stdin or argument
    payload_str = ""
    if len(sys.argv) > 1:
        payload_str = sys.argv[1]
    else:
        payload_str = sys.stdin.read().strip()

    if not payload_str:
        # If no input provided, allow
        sys.exit(0)

    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        # If raw command string was passed
        data = {"tool_name": "Bash", "tool_input": {"command": payload_str}}

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd()))

    # Extract command string depending on tool
    command_to_check = ""
    if isinstance(tool_input, dict):
        command_to_check = tool_input.get("command") or tool_input.get("query") or tool_input.get("sql") or ""
    elif isinstance(tool_input, str):
        command_to_check = tool_input

    if not command_to_check:
        sys.exit(0)

    # 2. Evaluate destructive rules
    is_blocked, reason = check_command(command_to_check)

    if is_blocked:
        log_blocked_command(command_to_check, project_path, reason)

        rejection_msg = (
            f"\n[CLAUDE HOOK BLOCKED] Execution Denied for Security Policy Violation!\n"
            f"--------------------------------------------------------------------\n"
            f"Reason       : {reason}\n"
            f"Command      : {command_to_check}\n"
            f"Project Path : {project_path}\n"
            f"Logged To    : {get_blocked_log_path()}\n"
            f"--------------------------------------------------------------------\n"
            f"Action: Rephrase command with explicit targets, safe git workflows,\n"
            f"or provide an explicit 'WHERE' clause on database mutations.\n"
        )
        try:
            sys.stderr.write(rejection_msg)
        except Exception:
            sys.stderr.write(rejection_msg.encode('ascii', 'replace').decode('ascii'))
        
        # Output structured JSON if caller expects JSON
        print(json.dumps({
            "allow": False,
            "blocked": True,
            "reason": reason,
            "command": command_to_check
        }))
        sys.exit(1)

    # Allow tool call
    sys.exit(0)

if __name__ == "__main__":
    main()
