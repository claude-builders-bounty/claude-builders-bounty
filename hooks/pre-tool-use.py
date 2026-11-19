#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Blocks destructive Bash and SQL commands.
"""

import sys
import os
import json
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r"\brm\s+-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b", "Destructive filesystem deletion: 'rm -rf'"),
    (r"\bDROP\s+TABLE\b", "Destructive SQL operation: 'DROP TABLE'"),
    (r"\bgit\s+push\s+(?:.*--force|-f\b)", "Destructive git operation: 'git push --force'"),
    (r"\bTRUNCATE(?:\s+TABLE)?\b", "Destructive SQL operation: 'TRUNCATE'"),
    (r"\bDELETE\s+FROM\s+(?!.*\bWHERE\b).*$", "Unbounded SQL deletion: 'DELETE FROM' without a WHERE clause")
]

def get_log_path():
    hooks_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    return os.path.join(hooks_dir, "blocked.log")

def log_blocked(cmd, reason, project_path):
    log_file = get_log_path()
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason} | Project: {project_path} | Command: {cmd}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def check_command(cmd_str, project_path):
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_str, re.IGNORECASE):
            log_blocked(cmd_str, reason, project_path)
            sys.stderr.write(f"\n[BLOCKED BY SECURITY HOOK] {reason}\nCommand: {cmd_str}\nOperation rejected for safety.\n")
            return False, reason
    return True, None

def main():
    raw_input = ""
    if not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()

    cmd = ""
    project_path = os.getcwd()

    if raw_input:
        try:
            data = json.loads(raw_input)
            cmd = data.get("input", {}).get("command", "") or data.get("command", "")
            project_path = data.get("project_path", project_path)
        except Exception:
            cmd = raw_input
    elif len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])

    if not cmd:
        sys.exit(0)

    allowed, reason = check_command(cmd, project_path)
    if not allowed:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
