#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Intercepts dangerous bash commands and logs violations to ~/.claude/hooks/blocked.log.
"""

import sys
import os
import json
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r"\brm\s+-[^\s]*r[^\s]*f\b|\brm\s+-[^\s]*f[^\s]*r\b|\brm\s+--recursive\s+--force\b|\brm\s+--force\s+--recursive\b", "Recursive forced deletion (rm -rf)"),
    (r"\bDROP\s+TABLE\b|\bDROP\s+DATABASE\b", "SQL DROP TABLE / DATABASE statement"),
    (r"\bTRUNCATE\b", "SQL TRUNCATE statement"),
    (r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b|\bgit\s+push\s+.*\+[\w/]+", "Forced git push (git push --force)")
]

def log_blocked(command: str, project_path: str, reason: str):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] [BLOCKED] Reason: {reason} | Path: {project_path} | Command: {command}\n"
    try:
        with open(log_file, "a") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def check_command(command: str, project_path: str = "."):
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, project_path, reason)
            return False, reason

    # Check for DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", command, re.IGNORECASE):
            reason = "Unbounded SQL DELETE without a WHERE clause"
            log_blocked(command, project_path, reason)
            return False, reason

    return True, ""

def main():
    command = ""
    project_path = os.getcwd()

    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read().strip()
            if raw:
                try:
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        tool_input = data.get("tool_input", {})
                        if isinstance(tool_input, dict):
                            command = tool_input.get("command", "")
                        elif isinstance(tool_input, str):
                            command = tool_input
                        project_path = data.get("project_path", project_path)
                    else:
                        command = str(data)
                except json.JSONDecodeError:
                    command = raw
        except Exception:
            pass

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        sys.exit(0)

    is_allowed, reason = check_command(command, project_path)
    if not is_allowed:
        error_msg = f"SECURITY BLOCK: The bash command '{command}' was intercepted because it matches a prohibited destructive pattern ({reason})."
        sys.stderr.write(f"{error_msg}\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
