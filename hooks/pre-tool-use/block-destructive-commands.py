#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Intersects and blocks dangerous bash/shell invocations before execution.
Complies with Claude Code hook protocols (~/.claude/hooks/).
"""

import sys
import os
import json
import re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns to intercept
DESTRUCTIVE_RULES = [
    {
        "name": "Recursive Force Removal (rm -rf)",
        "pattern": re.compile(
            r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+|--(?:recursive|force)\s+)*"
            r"(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-[a-zA-Z]*r\b.*-[a-zA-Z]*f\b|-[a-zA-Z]*f\b.*-[a-zA-Z]*r\b|--recursive.*--force|--force.*--recursive)",
            re.IGNORECASE,
        ),
        "reason": "Indiscriminate recursive file deletion (rm -rf) is blocked for safety."
    },
    {
        "name": "SQL DROP TABLE",
        "pattern": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "reason": "Destructive DDL query 'DROP TABLE' causes unrecoverable schema & data loss."
    },
    {
        "name": "Git Force Push",
        "pattern": re.compile(r"\bgit\s+push\b.*?(?:--force|-f\b|--force-with-lease)", re.IGNORECASE),
        "reason": "Force-pushing overwrites remote history and can destroy team commits."
    },
    {
        "name": "SQL TRUNCATE",
        "pattern": re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
        "reason": "Table truncation permanently empties database records without row-level rollback."
    },
]

def check_delete_without_where(command: str) -> tuple[bool, str]:
    """
    Checks if command contains 'DELETE FROM' without a qualifying 'WHERE' clause.
    """
    delete_matches = list(re.finditer(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_\.\"'`]+)", command, re.IGNORECASE))
    if not delete_matches:
        return False, ""

    for match in delete_matches:
        # Check text from match start to semicolon or end of string
        tail = command[match.start():]
        statement_end = tail.find(";")
        statement = tail[:statement_end] if statement_end != -1 else tail
        if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
            return True, f"Unbounded 'DELETE FROM {match.group(1)}' without a WHERE clause is blocked."
            
    return False, ""

def evaluate_command(command: str) -> tuple[bool, str, str]:
    """
    Evaluates whether a command contains destructive patterns.
    Returns: (is_blocked: bool, rule_name: str, reason: str)
    """
    if not command:
        return False, "", ""

    # Check rule patterns
    for rule in DESTRUCTIVE_RULES:
        if rule["pattern"].search(command):
            return True, rule["name"], rule["reason"]

    # Check DELETE FROM without WHERE
    is_delete_blocked, reason = check_delete_without_where(command)
    if is_delete_blocked:
        return True, "SQL DELETE FROM without WHERE", reason

    return False, "", ""

def log_blocked_attempt(command: str, rule_name: str, project_path: str):
    """
    Appends audit log entry to ~/.claude/hooks/blocked.log
    """
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = (
            f"[{timestamp}] PROJECT: {project_path} | "
            f"RULE: {rule_name} | "
            f"COMMAND: {command.strip()}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[WARNING] Could not write to blocked.log: {e}\n")

def extract_command_from_payload(raw_input: str) -> tuple[str, str]:
    """
    Extracts the tool command and tool name from Claude Code JSON payload or raw string.
    Returns: (tool_name, command)
    """
    if not raw_input.strip():
        return "", ""

    try:
        data = json.loads(raw_input)
        if isinstance(data, dict):
            tool_name = data.get("tool_name") or data.get("tool") or ""
            tool_input = data.get("tool_input") or {}
            
            if isinstance(tool_input, dict):
                command = tool_input.get("command") or tool_input.get("cmd") or ""
            elif isinstance(tool_input, str):
                command = tool_input
            else:
                command = ""
                
            return tool_name, command
    except Exception:
        # Not JSON, treat raw_input as command directly
        pass

    return "Bash", raw_input.strip()

def main():
    raw_payload = ""
    # 1. Read from stdin if piped
    if not sys.stdin.isatty():
        try:
            raw_payload = sys.stdin.read()
        except Exception:
            raw_payload = ""

    # 2. Fall back to CLI argument if stdin is empty
    if not raw_payload.strip() and len(sys.argv) > 1:
        raw_payload = " ".join(sys.argv[1:])

    if not raw_payload.strip():
        # Nothing to check, allow execution
        sys.exit(0)

    tool_name, command = extract_command_from_payload(raw_payload)

    # If payload is for non-shell tool, allow it
    if tool_name and tool_name.lower() not in ("bash", "sh", "terminal", "exec", "command", "shell"):
        sys.exit(0)

    if not command:
        sys.exit(0)

    # 3. Evaluate command for destructive patterns
    is_blocked, rule_name, reason = evaluate_command(command)

    if is_blocked:
        project_path = os.environ.get("CLAUDE_PROJECT_PATH", os.getcwd())
        log_blocked_attempt(command, rule_name, project_path)

        # Output detailed explanation to stderr for Claude Code
        error_msg = (
            f"\n=======================================================\n"
            f"[PRE-TOOL-USE SECURITY HOOK] EXECUTION BLOCKED\n"
            f"=======================================================\n"
            f"Attempted Command: {command}\n"
            f"Violation:         {rule_name}\n"
            f"Reason:            {reason}\n"
            f"Audit Trail:       Logged to {LOG_FILE}\n"
            f"=======================================================\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)

    # Allowed command
    sys.exit(0)

if __name__ == "__main__":
    main()
