#!/usr/bin/env python3
"""
Pre-Tool-Use Hook: Blocks Destructive Bash & SQL Commands
Protects terminal and execution environments from high-risk accidental wipes.
"""
import sys
import os
import re
import json
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns required by acceptance criteria:
# - rm -rf
# - DROP TABLE
# - git push --force (or -f)
# - TRUNCATE
# - DELETE FROM without WHERE
BLOCKED_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", "Dangerous recursive force delete ('rm -rf')"),
    (r"\bDROP\s+TABLE\b", "Destructive SQL operation ('DROP TABLE')"),
    (r"\bgit\s+push\b.*(--force|-f)\b", "Destructive remote history rewrite ('git push --force')"),
    (r"\bTRUNCATE\s+TABLE\b|\bTRUNCATE\b", "Destructive table wipe ('TRUNCATE')"),
    (r"\bDELETE\s+FROM\s+[\w\.\"]+(?!\s+WHERE\b)", "Unconstrained table deletion ('DELETE FROM' without WHERE clause)")
]

def log_blocked_attempt(command: str, reason: str):
    """Logs the blocked attempt with timestamp, attempted command, and working directory"""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.utcnow().isoformat() + "Z"
        cwd = os.getcwd()
        log_entry = f"[{timestamp}] REJECTED: {reason} | CWD: {cwd} | CMD: {command}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked log: {e}\n")

def check_command(cmd_string: str):
    """Inspects command against destructive patterns"""
    # 1. Check rm -rf
    if re.search(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", cmd_string, re.IGNORECASE):
        reason = "Dangerous recursive force delete ('rm -rf')"
        log_blocked_attempt(cmd_string, reason)
        return False, reason

    # 2. Check DROP TABLE
    if re.search(r"\bDROP\s+TABLE\b", cmd_string, re.IGNORECASE):
        reason = "Destructive SQL operation ('DROP TABLE')"
        log_blocked_attempt(cmd_string, reason)
        return False, reason

    # 3. Check git push --force / -f
    if re.search(r"\bgit\s+push\b.*(--force|-f)\b", cmd_string, re.IGNORECASE):
        reason = "Destructive remote history rewrite ('git push --force')"
        log_blocked_attempt(cmd_string, reason)
        return False, reason

    # 4. Check TRUNCATE
    if re.search(r"\bTRUNCATE\b", cmd_string, re.IGNORECASE):
        reason = "Destructive table wipe ('TRUNCATE')"
        log_blocked_attempt(cmd_string, reason)
        return False, reason

    # 5. Check DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", cmd_string, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", cmd_string, re.IGNORECASE):
            reason = "Unconstrained table deletion ('DELETE FROM' without WHERE clause)"
            log_blocked_attempt(cmd_string, reason)
            return False, reason

    return True, "ALLOWED"

def main():
    # Read payload from standard input (Claude Code Pre-Tool-Use contract)
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)
        
        # Parse tool payload
        try:
            payload = json.loads(raw_input)
            tool_name = payload.get("tool_name", "")
            tool_input = payload.get("tool_input", {})
            command = tool_input.get("command", "") or tool_input.get("cmd", "") or ""
        except Exception:
            command = raw_input

        if not command:
            sys.exit(0)

        is_allowed, reason = check_command(command)
        if not is_allowed:
            error_message = (
                f"\n🚫 [BLOCKED BY SECURITY HOOK]: {reason}\n"
                f"Attempted Command: {command}\n"
                f"Logged to: ~/.claude/hooks/blocked.log\n"
                f"Action Refused: Destructive command rejected to protect repository and database integrity.\n"
            )
            sys.stderr.write(error_message)
            sys.exit(1)

        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Pre-tool-use hook exception: {e}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
