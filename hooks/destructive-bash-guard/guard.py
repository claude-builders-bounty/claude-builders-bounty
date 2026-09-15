#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Guard
Intercepts and blocks destructive bash/shell commands before execution.
Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import sys
import os
import re
import json
from datetime import datetime, timezone

DANGEROUS_PATTERNS = [
    (
        re.compile(r'\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\b|\brm\s+--(?:recursive|force)\b', re.IGNORECASE),
        "Recursive and forced deletion ('rm -rf') is prohibited."
    ),
    (
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        "Database destructive command ('DROP TABLE') is prohibited."
    ),
    (
        re.compile(r'\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_`"\'\.]+', re.IGNORECASE),
        "Database table truncation ('TRUNCATE') is prohibited."
    ),
    (
        re.compile(r'\bgit\s+push\s+.*?(?:-f\b|--force\b|--force-with-lease\b)', re.IGNORECASE),
        "Force-pushing to remote git branches ('git push --force') is prohibited."
    )
]

def check_delete_without_where(command_str):
    for match in re.finditer(r'\bDELETE\s+FROM\s+([a-zA-Z0-9_`"\'\.]+)(.*?)(?:;|$)', command_str, re.IGNORECASE):
        after_clause = match.group(2)
        if not re.search(r'\bWHERE\b', after_clause, re.IGNORECASE):
            return True
    return False

def log_blocked(command, cwd):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] BLOCKED: {command} | DIR: {cwd}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to blocked.log: {e}\n")

def check_command(command_str, cwd=None):
    if not command_str:
        return True, ""
    
    if cwd is None:
        cwd = os.getcwd()

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command_str):
            log_blocked(command_str, cwd)
            return False, reason

    if check_delete_without_where(command_str):
        reason = "Unrestricted table wipe ('DELETE FROM' without WHERE clause) is prohibited."
        log_blocked(command_str, cwd)
        return False, reason

    return True, ""

def main():
    cwd = os.getcwd()
    command_to_check = ""

    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    command_to_check = (
                        payload.get("command") or 
                        payload.get("tool_input", {}).get("command") or 
                        payload.get("parameters", {}).get("command") or 
                        raw_input
                    )
                    cwd = payload.get("cwd") or payload.get("project_path") or cwd
                except json.JSONDecodeError:
                    command_to_check = raw_input
        except Exception:
            pass

    if not command_to_check and len(sys.argv) > 1:
        command_to_check = " ".join(sys.argv[1:])

    is_safe, reason = check_command(command_to_check, cwd)
    if not is_safe:
        sys.stderr.write("\n" + "=" * 65 + "\n")
        sys.stderr.write("🚨 CLAUDE CODE SAFETY HOOK: COMMAND INTERCEPTED & BLOCKED\n")
        sys.stderr.write("=" * 65 + "\n")
        sys.stderr.write(f"Attempted Command: {command_to_check}\n")
        sys.stderr.write(f"Security Reason:   {reason}\n")
        sys.stderr.write(f"Log written to:    ~/.claude/hooks/blocked.log\n")
        sys.stderr.write("=" * 65 + "\n\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
