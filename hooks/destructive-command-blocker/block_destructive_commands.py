#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns required by Bounty #3
DANGEROUS_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", "Recursive forced file deletion (rm -rf)"),
    (r"\bgit\s+push\b.*(--force|-f)\b", "Forced git push (git push --force)"),
    (r"(?i)\bDROP\s+TABLE\b", "SQL destructive query (DROP TABLE)"),
    (r"(?i)\bTRUNCATE\b", "SQL table purge (TRUNCATE)"),
    (r"(?i)\bDELETE\s+FROM\s+\w+\b(?!\s+WHERE\b)", "Unrestricted SQL deletion (DELETE FROM without WHERE)")
]

def log_blocked(command: str, reason: str, cwd: str):
    os.makedirs(os.path.dirname(BLOCKED_LOG_PATH), exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    log_entry = (
        f"[{timestamp}] BLOCKED: {reason}\n"
        f"  Project: {cwd}\n"
        f"  Command: {command}\n"
        f"{'-'*60}\n"
    )
    with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)

def check_command(command: str, cwd: str = "") -> tuple[bool, str]:
    if not command:
        return False, ""
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return True, description
    return False, ""

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        data = json.loads(raw_input)
    except Exception:
        sys.exit(0)

    tool_input = data.get("tool_input") or data.get("input") or {}
    command = tool_input.get("command", "")
    cwd = tool_input.get("cwd", os.getcwd())

    is_blocked, reason = check_command(command, cwd)
    if is_blocked:
        log_blocked(command, reason, cwd)
        sys.stderr.write(
            f"\n[SECURITY HOOK ERROR] Destructive bash command blocked by policy.\n"
            f"Reason: {reason}\n"
            f"Command: {command}\n"
            f"Logged to: {BLOCKED_LOG_PATH}\n\n"
        )
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
