#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code — blocks destructive bash commands.

Blocks:
  - rm -rf / rm -fr / rm --recursive --force
  - DROP TABLE / DROP DATABASE
  - TRUNCATE / TRUNCATE TABLE
  - DELETE FROM ... without WHERE clause
  - git push --force / git push -f

Logs blocked attempts to ~/.claude/hooks/blocked.log
Returns standard Claude Code hook decision: 'block' or 'allow'
"""
import datetime
import json
import os
import re
import sys

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")

BLOCKED_PATTERNS = [
    (
        re.compile(
            r"\brm\s+(?:.*-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)|.*(?:-r\s+.*-f|-f\s+.*-r|--recursive|--force))",
            re.IGNORECASE,
        ),
        "DESTRUCTIVE: 'rm' with recursive/force flags can permanently destroy unrecoverable data. Please specify exact paths or avoid -rf flags.",
    ),
    (
        re.compile(r"\bDROP\s+(?:TABLE|DATABASE)\b", re.IGNORECASE),
        "DESTRUCTIVE SQL: 'DROP TABLE/DATABASE' irreversibly destroys database schemas and records.",
    ),
    (
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
        "DESTRUCTIVE SQL: 'TRUNCATE' clears all records from the target table irrecoverably.",
    ),
    (
        re.compile(r"\bDELETE\s+FROM\s+[^\s;]+(?:\s*;|\s*$)(?!.*\bWHERE\b)", re.IGNORECASE),
        "DESTRUCTIVE SQL: 'DELETE FROM' without a WHERE clause will delete every row in the table.",
    ),
    (
        re.compile(r"\bgit\s+push\b.*(?:\-f\b|--force\b|--force-with-lease\b)", re.IGNORECASE),
        "DESTRUCTIVE GIT: Force-pushing can overwrite remote branch history and erase team commits.",
    ),
]


def check_command_blocked(command: str):
    """Returns the blocking reason if command matches a destructive pattern, else None."""
    if not command:
        return None
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def get_project_root():
    """Detects current git project root or fallback to cwd."""
    cur = os.getcwd()
    while cur and cur != os.path.dirname(cur):
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        cur = os.path.dirname(cur)
    return os.getcwd()


def log_blocked_command(command: str, reason: str):
    """Appends blocked command details to ~/.claude/hooks/blocked.log in JSON format."""
    try:
        os.makedirs(HOOKS_DIR, exist_ok=True)
        record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "attempted_command": command,
            "project_path": get_project_root(),
            "reason": reason,
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        # Prevent hook from failing due to logging errors
        pass


def evaluate_hook(payload: dict) -> dict:
    """Evaluates payload and returns standard Claude Code hook decision."""
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

    if tool_name == "Bash" and isinstance(command, str) and command.strip():
        reason = check_command_blocked(command.strip())
        if reason:
            log_blocked_command(command.strip(), reason)
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "block",
                    "reason": reason,
                }
            }

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
    }


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    result = evaluate_hook(payload)
    print(json.dumps(result))
    if result["hookSpecificOutput"].get("permissionDecision") == "block":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
