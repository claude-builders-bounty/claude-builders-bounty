#!/usr/bin/env python3
"""Pre-tool-use hook for Claude Code that blocks destructive bash commands.

Reads stdin JSON from Claude Code hooks and blocks dangerous patterns like
rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE without WHERE.

Hook format (Claude Code):
  Input:  JSON on stdin with {tool_name, tool_input, ...}
  Output: JSON on stdout: {"decision": "block", "reason": "..."} or {"decision": "allow"}
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    # rm -rf variants
    (re.compile(r"\brm\s+.*-[a-zA-Z]*f[a-zA-Z]*\s+", re.IGNORECASE), "rm with force flag detected"),
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+", re.IGNORECASE), "rm with recursive flag detected"),
    # DROP TABLE
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE detected"),
    # git push --force
    (re.compile(r"\bgit\s+push\s+.*--force", re.IGNORECASE), "git push --force detected"),
    (re.compile(r"\bgit\s+push\s+.*-\w*f", re.IGNORECASE), "git push -f detected"),
    # TRUNCATE
    (re.compile(r"\bTRUNCATE\s+TABLE?\b", re.IGNORECASE), "TRUNCATE detected"),
    (re.compile(r"\bTRUNCATE\s+\w+", re.IGNORECASE), "TRUNCATE detected"),
    # DELETE without WHERE
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;", re.IGNORECASE), "DELETE FROM without WHERE clause detected"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*$", re.IGNORECASE | re.MULTILINE), "DELETE FROM without WHERE clause detected"),
]

# SQL comment pattern — strip single-line comments for SQL analysis
SQL_COMMENT = re.compile(r"--[^\n]*", re.MULTILINE)


def normalize_command(cmd: str) -> str:
    """Normalize command string for pattern matching."""
    # Strip SQL comments for SQL-related checks
    cleaned = SQL_COMMENT.sub("", cmd)
    return cleaned


def check_delete_without_where(cmd: str) -> str | None:
    """Special check: DELETE FROM ... without WHERE clause."""
    normalized = normalize_command(cmd)
    # Find DELETE FROM statements
    delete_pattern = re.compile(r"\bDELETE\s+FROM\s+[\w\"`']+", re.IGNORECASE)
    for match in delete_pattern.finditer(normalized):
        # Check if there's a WHERE after this match
        rest = normalized[match.end():]
        if not re.search(r"\bWHERE\b", rest, re.IGNORECASE):
            return "DELETE FROM without WHERE clause detected"
    return None


def check_command(cmd: str) -> str | None:
    """Check if a command should be blocked. Returns reason or None."""
    # Check static patterns
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(cmd):
            # For DELETE patterns, use more nuanced check
            if "DELETE" in reason.upper():
                continue  # handled by check_delete_without_where
            return reason

    # Check DELETE without WHERE
    result = check_delete_without_where(cmd)
    if result:
        return result

    return None


def log_blocked(command: str, reason: str, project_path: str = "") -> None:
    """Log a blocked attempt to the log file."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log_entry = f"[{timestamp}] BLOCKED: {reason} | command: {command[:200]} | project: {project_path}\n"
    with open(LOG_PATH, "a") as f:
        f.write(log_entry)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"decision": "allow"}))
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    project_path = data.get("project_path", "")

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        print(json.dumps({"decision": "allow"}))
        return

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    # Check the full command first (handles multiline SQL with WHERE on next line)
    reason = check_command(command)
    if reason:
        log_blocked(command, reason, project_path)
        print(json.dumps({"decision": "block", "reason": f"⛔ Blocked: {reason}. This command was not executed."}))
        return

    # Check individual lines for shell-destructive commands (rm, git push)
    shell_patterns = [(p, r) for p, r in BLOCKED_PATTERNS if "DELETE" not in r.upper()]
    for line in command.split("\n"):
        line = line.strip()
        if not line:
            continue
        for pattern, reason in shell_patterns:
            if pattern.search(line):
                log_blocked(command, reason, project_path)
                print(json.dumps({"decision": "block", "reason": f"⛔ Blocked: {reason}. This command was not executed."}))
                return

    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
