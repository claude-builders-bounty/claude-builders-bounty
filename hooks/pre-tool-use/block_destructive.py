#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Prevents accidental execution of dangerous commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE without WHERE).
"""
import sys
import re
import os
import json
from datetime import datetime

BLOCKED_PATTERNS = [
    (r'\brm\s+((-[a-zA-Z]*[rf][a-zA-Z]*\s+-[a-zA-Z]*[rf][a-zA-Z]*)|(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*)|(-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*))\b', "Recursive force removal (`rm -rf` / `rm -fr`) is prohibited."),
    (r'\bDROP\s+TABLE\b', "Dropping database tables (`DROP TABLE`) is prohibited."),
    (r'\bgit\s+push\b.*(\s+--force\b|\s+-f\b)', "Force-pushing git branches (`git push --force` / `-f`) is prohibited."),
    (r'\bTRUNCATE(\s+TABLE)?\b', "Table truncation (`TRUNCATE`) is prohibited."),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "Deleting records without an explicit `WHERE` clause is prohibited.")
]

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

def log_blocked(command: str, project_path: str, reason: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = f"[{timestamp}] PROJECT={project_path} REASON={reason} COMMAND={command}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def evaluate_command(command: str) -> tuple[bool, str]:
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason
    return True, "Allowed"

def main():
    # Claude Code hooks deliver context via JSON on stdin or CLI arguments
    raw_input = sys.stdin.read().strip()
    command = ""
    project_path = os.getcwd()

    if raw_input:
        try:
            payload = json.loads(raw_input)
            command = payload.get("command") or payload.get("input", {}).get("command", "")
            project_path = payload.get("cwd") or payload.get("project_path") or os.getcwd()
        except json.JSONDecodeError:
            command = raw_input

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        sys.exit(0)

    is_allowed, reason = evaluate_command(command)
    if not is_allowed:
        log_blocked(command, project_path, reason)
        print(f"\n🛑 [BLOCKED BY CLAUDE CODE HOOK]: {reason}", file=sys.stderr)
        print(f"Attempted Command: {command}", file=sys.stderr)
        print(f"Logged to: {LOG_FILE}\n", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
