#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code to block destructive bash commands.
Blocks dangerous command patterns and logs blocked attempts.
"""

import sys
import os
import json
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r"\brm\s+-[^\s]*r[^\s]*f\b", "Recursive forced file deletion (rm -rf) is blocked."),
    (r"\brm\s+-[^\s]*f[^\s]*r\b", "Recursive forced file deletion (rm -fr) is blocked."),
    (r"\brm\s+--recursive\s+--force\b", "Recursive forced file deletion is blocked."),
    (r"\bgit\s+push\s+.*(--force|-f)\b", "Force-pushing to remote git branches (git push --force) is blocked."),
    (r"\bDROP\s+TABLE\b", "Destructive SQL operation (DROP TABLE) is blocked."),
    (r"\bDROP\s+DATABASE\b", "Destructive SQL operation (DROP DATABASE) is blocked."),
    (r"\bTRUNCATE(\s+TABLE)?\b", "Destructive SQL operation (TRUNCATE) is blocked."),
    (r"\bDELETE\s+FROM\s+\w+\s*(;|$)(?!\s*WHERE\b)", "Unrestricted SQL deletion without WHERE clause is blocked."),
]

def log_blocked(command: str, cwd: str, reason: str):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] [BLOCKED] Reason: {reason} | CWD: {cwd} | Command: {command}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Failed to write to blocked.log: {e}\n")

def main():
    # Hook receives JSON payload from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
        payload = json.loads(input_data)
    except Exception:
        # If payload is plain text or raw args
        payload = {"tool_name": "Bash", "tool_input": {"command": " ".join(sys.argv[1:])}}

    tool_name = payload.get("tool_name", "") or payload.get("tool", "")
    tool_input = payload.get("tool_input", {}) or payload.get("parameters", {})
    
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "") or tool_input.get("cmd", "")
    elif isinstance(tool_input, str):
        command = tool_input

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    cwd = payload.get("cwd", os.getcwd())

    if tool_name.lower() in ["bash", "terminal", "execute_command", "shell", ""] and command:
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                log_blocked(command, cwd, reason)
                sys.stderr.write(f"\n🚨 [HOOK BLOCKED] {reason}\nAttempted command: `{command}`\nOperation was aborted for safety.\n\n")
                sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
