#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Bash Command Blocker
Intercepts dangerous shell commands (rm -rf, DROP TABLE, git push --force,
TRUNCATE, DELETE FROM without WHERE) before Claude Code executes them.

Conforms to Claude Code PreToolUse hook specifications.
"""

import sys
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path


# Regex patterns and security justifications for blocked command classes
BLOCKED_PATTERNS = [
    # 1. Recursive forced file deletion: rm -rf, rm -fr, rm -r -f, rm --recursive --force, etc.
    (
        r"(?:^|[;&|]\s*)\brm\s+(?:-[a-zA-Z0-9_-]*[rR][a-zA-Z0-9_-]*[fF][a-zA-Z0-9_-]*|-[a-zA-Z0-9_-]*[fF][a-zA-Z0-9_-]*[rR][a-zA-Z0-9_-]*|--recursive\s+--force|--force\s+--recursive|-[rR]\s+-[fF]|-[fF]\s+-[rR])\b",
        "Recursive forced deletion ('rm -rf') can permanently wipe project files, directories, or system paths without recovery.",
    ),
    # 2. Database table / schema drops: DROP TABLE / DROP DATABASE
    (
        r"\bDROP\s+(?:TEMPORARY\s+)?(?:TABLE|DATABASE|SCHEMA)\b",
        "Destructive DDL statement ('DROP TABLE / DATABASE') destroys database tables, schemas, and relational structures.",
    ),
    # 3. Forced git push: git push -f, git push --force, git push --force-with-lease
    (
        r"\bgit\s+push\b[^\n;&|]*(?:--force\b|--force-with-lease\b|-f\b)",
        "Forced git push ('git push --force') can permanently overwrite upstream commits and clobber team history.",
    ),
    # 4. Table truncation: TRUNCATE [TABLE]
    (
        r"\bTRUNCATE(?:\s+TABLE)?\s+[a-zA-Z0-9_.]+",
        "Destructive SQL statement ('TRUNCATE TABLE') wipes all table rows without invoking transaction delete triggers.",
    ),
]


def check_unbounded_delete(command: str) -> str | None:
    """
    Checks for SQL 'DELETE FROM <table>' statements lacking an accompanying WHERE clause.
    Splits multi-statement inputs by semicolon or newline.
    """
    # Clean SQL quotes or subqueries to inspect statements
    statements = re.split(r"[;\n]", command)
    for stmt in statements:
        stripped = stmt.strip()
        # Look for DELETE FROM <table>
        delete_match = re.search(r"\bDELETE\s+FROM\s+([`\"']?[a-zA-Z0-9_.]+[`\"']?)", stripped, re.IGNORECASE)
        if delete_match:
            # Check if there is a WHERE clause in this statement
            if not re.search(r"\bWHERE\b", stripped, re.IGNORECASE):
                table_name = delete_match.group(1)
                return (
                    f"Unbounded 'DELETE FROM {table_name}' without a WHERE clause will delete all records in the table. "
                    "Specify an explicit WHERE condition to limit row impact."
                )
    return None


def inspect_command(command: str) -> str | None:
    """
    Inspects command string against security rules.
    Returns explanation reason if command must be blocked, or None if safe.
    """
    if not command or not isinstance(command, str):
        return None

    # Check primary regex patterns
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason

    # Check unbounded DELETE FROM
    delete_reason = check_unbounded_delete(command)
    if delete_reason:
        return delete_reason

    return None


def get_log_file_path() -> Path:
    """
    Resolves path to ~/.claude/hooks/blocked.log
    """
    home = Path(os.environ.get("HOME") or Path.home())
    log_dir = home / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "blocked.log"


def log_blocked_attempt(command: str, project_path: str, reason: str):
    """
    Appends audit entry to ~/.claude/hooks/blocked.log with timestamp,
    attempted command, project path, and reason.
    """
    try:
        log_path = get_log_file_path()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "project_path": project_path,
            "reason": reason,
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        sys.stderr.write(f"[pre-tool-use-hook] Warning: could not write to audit log: {e}\n")


def main():
    """
    Main hook entrypoint for Claude Code PreToolUse event.
    """
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        # No input passed; exit cleanly
        sys.exit(0)

    try:
        payload = json.loads(raw_input)
    except Exception:
        # Fallback: treat raw string as command if not JSON
        payload = {"tool_input": {"command": raw_input.strip()}}

    # Extract command and context
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or payload.get("command") or ""
    project_path = payload.get("cwd") or os.getcwd()

    reason = inspect_command(command)

    if reason:
        # Log the blocked attempt
        log_blocked_attempt(command, project_path, reason)

        # Output Claude Code PreToolUse denial payload
        denial_message = (
            f"🚫 [BLOCKED BY SECURITY POLICY] Command was rejected:\n"
            f"Command: {command}\n"
            f"Reason: {reason}\n\n"
            f"Please revise your tool call to use a safer alternative (e.g. targeted rm on specific files, "
            f"explicit SQL WHERE clause, or regular git push)."
        )

        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": denial_message,
            }
        }
        print(json.dumps(response, indent=2))
        sys.exit(0)

    # Allowed: return empty JSON or exit 0
    sys.exit(0)


if __name__ == "__main__":
    main()
