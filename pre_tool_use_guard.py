#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Blocks Destructive Bash Commands
Compliant with Claude Code hook specifications (~/.claude/hooks/)
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

# Log file path
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# Destructive pattern rules: (Regex pattern, Description/Reason)
DANGEROUS_PATTERNS = [
    (
        r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b',
        "Recursive force removal ('rm -rf') is blocked to protect project filesystem."
    ),
    (
        r'\bgit\s+push\s+.*(--force|-f\b)',
        "Forced git push ('git push --force' / '-f') is blocked to prevent history overwrites."
    ),
    (
        r'\bDROP\s+TABLE\b',
        "SQL DDL command 'DROP TABLE' is blocked to prevent accidental database destruction."
    ),
    (
        r'\bTRUNCATE(?:\s+TABLE)?\b',
        "SQL command 'TRUNCATE' is blocked to prevent unrecoverable data wiping."
    ),
    (
        r'\bDELETE\s+FROM\s+["`\w]+(?!\s*(?:WHERE\b|;|\Z|\n))(?:\s*;|\s*\Z|\s*--|\s*/\*)',
        "SQL command 'DELETE FROM' without a WHERE clause is blocked to prevent total table data loss."
    )
]

def check_command_safety(cmd: str):
    """
    Checks if a shell command contains dangerous patterns.
    Returns (is_blocked: bool, reason: str, matched_pattern: str)
    """
    if not cmd:
        return False, "", ""
    
    # Check special case: DELETE FROM without WHERE
    # Normalize spaces
    clean_cmd = " ".join(cmd.split())
    
    # Check DELETE FROM without WHERE
    if re.search(r'\bDELETE\s+FROM\b', clean_cmd, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', clean_cmd, re.IGNORECASE):
            return True, "SQL command 'DELETE FROM' without a WHERE clause is blocked to prevent total table data loss.", "DELETE FROM (missing WHERE)"

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.startswith(r'\bDELETE'):
            continue
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, reason, pattern

    return False, "", ""

def log_blocked_attempt(command: str, project_path: str, reason: str):
    """Logs blocked attempts with timestamp, command, and project path."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] BLOCKED: \"{command}\" | Project: {project_path} | Reason: {reason}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked log: {e}\n")

def main():
    project_path = os.getcwd()
    
    # Claude Code passes tool call information via STDIN or CLI arguments
    raw_input = ""
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
        except Exception:
            pass

    command_to_check = ""
    
    if raw_input:
        try:
            data = json.loads(raw_input)
            # Handle standard Claude Code pre-tool-use payload
            if isinstance(data, dict):
                tool_name = data.get("tool_name") or data.get("tool", "")
                tool_input = data.get("tool_input") or data.get("input", {})
                if tool_name in ["bash", "execute_command", "terminal", "sh"]:
                    if isinstance(tool_input, dict):
                        command_to_check = tool_input.get("command") or tool_input.get("cmd", "")
                    elif isinstance(tool_input, str):
                        command_to_check = tool_input
                elif "command" in data:
                    command_to_check = data["command"]
        except Exception:
            command_to_check = raw_input.strip()

    # Fallback to CLI args
    if not command_to_check and len(sys.argv) > 1:
        command_to_check = " ".join(sys.argv[1:])

    if not command_to_check:
        # Nothing to validate, let it pass
        sys.exit(0)

    is_blocked, reason, matched = check_command_safety(command_to_check)

    if is_blocked:
        log_blocked_attempt(command_to_check, project_path, reason)
        error_msg = (
            f"\n⛔ [SECURITY HOOK BLOCKED] Destructive command detected!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Attempted: {command_to_check}\n"
            f"Reason:    {reason}\n"
            f"Logged to: {LOG_FILE}\n"
            f"Action:    Execution aborted to prevent irreversible system/data damage.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)

    # Safe command
    sys.exit(0)

if __name__ == "__main__":
    main()
