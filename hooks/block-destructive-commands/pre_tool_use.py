#!/usr/bin/env python3
"""
pre_tool_use.py — Claude Code Pre-Tool-Use Destructive Command Interceptor
Intercepts and blocks dangerous bash commands before execution in Claude Code.
Logs blocked attempts to ~/.claude/hooks/blocked.log.
"""

import sys
import os
import re
import json
from datetime import datetime
from typing import Tuple, Optional, List

def split_statements(command: str) -> List[str]:
    """Splits command chain by ; && || and newlines."""
    # Split by ;, &&, ||, and newline
    parts = re.split(r";|&&|\|\||\n", command)
    return [p.strip() for p in parts if p.strip()]

def check_rm_rf(statement: str) -> bool:
    """Detects recursive force removal variants (rm -rf, rm -fr, rm -r -f, rm -f -r, etc.)."""
    # Ignore pure echo/printf statements
    if re.match(r"^(?:echo|printf)\s+", statement):
        return False

    rm_match = re.search(r"\brm\s+([^;&|]+)", statement)
    if rm_match:
        args = rm_match.group(1)
        has_r = bool(re.search(r"(?:^|\s)(?:-[a-zA-Z0-9]*r[a-zA-Z0-9]*|--recursive|-R)\b", args))
        has_f = bool(re.search(r"(?:^|\s)(?:-[a-zA-Z0-9]*f[a-zA-Z0-9]*|--force)\b", args))
        if has_r and has_f:
            return True
    return False

def check_git_force(statement: str) -> bool:
    """Detects git push with force flags."""
    if re.match(r"^(?:echo|printf)\s+", statement):
        return False
    return bool(re.search(r"\bgit\s+push\b.*(?:\s+-f\b|\s+--force\b|\s+--force-with-lease\b)", statement))

def strip_quotes(text: str) -> str:
    """Replaces quoted string contents with empty quotes to prevent false positives in string literals."""
    text = re.sub(r"'[^']*'", "''", text)
    text = re.sub(r'"[^"]*"', '""', text)
    return text

def check_sql_statement(statement: str) -> Tuple[bool, Optional[str]]:
    """Checks an individual statement for destructive SQL keywords."""
    if re.match(r"^(?:echo|printf)\s+", statement):
        return False, None

    code = strip_quotes(statement)
    if not code.strip():
        return False, None

    # Check DROP TABLE/DATABASE/SCHEMA/VIEW
    if re.search(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA|VIEW)\b", code, re.IGNORECASE):
        return True, "SQL DROP operations are forbidden in automated commands without manual review."

    # Check TRUNCATE
    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\s+[a-zA-Z0-9_`\"']+", code, re.IGNORECASE):
        return True, "SQL TRUNCATE statements are forbidden to prevent bulk unrecoverable table wiping."

    # Check DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"']+", code, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", code, re.IGNORECASE):
            return True, "SQL 'DELETE FROM' without a WHERE clause is forbidden to prevent complete data erasure."

    return False, None

def inspect_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Evaluates a command against all security rules across all chained statements.
    Returns (is_blocked, reason).
    """
    statements = split_statements(command)
    for stmt in statements:
        if check_rm_rf(stmt):
            return True, "Recursive force removal ('rm -rf') is forbidden to prevent accidental data loss."

        if check_git_force(stmt):
            return True, "Force-pushing git history ('git push --force') is forbidden to preserve repository integrity."

        is_sql_blocked, sql_reason = check_sql_statement(stmt)
        if is_sql_blocked:
            return True, sql_reason

    return False, None

def get_log_path() -> str:
    override = os.getenv("BLOCKED_LOG_PATH")
    if override:
        return override
    home = os.path.expanduser("~")
    hooks_dir = os.path.join(home, ".claude", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    return os.path.join(hooks_dir, "blocked.log")

def log_blocked_attempt(command: str, reason: str, cwd: Optional[str] = None):
    log_file = get_log_path()
    timestamp = datetime.now().isoformat()
    project_path = cwd or os.getcwd()
    entry = f"[{timestamp}] BLOCKED: \"{command}\" | REASON: {reason} | PATH: {project_path}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to write to blocked.log: {e}\n")

def extract_command_from_payload(raw_input: str) -> str:
    """Extracts command from JSON payload or returns raw input string."""
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict):
            tool_input = data.get("tool_input", {})
            if isinstance(tool_input, dict) and "command" in tool_input:
                return tool_input["command"]
            if "command" in data:
                return data["command"]
    except Exception:
        pass
    return raw_input.strip()

def main():
    raw_input = ""
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read()

    if not raw_input.strip():
        sys.exit(0)

    command = extract_command_from_payload(raw_input)
    is_blocked, reason = inspect_command(command)

    if is_blocked:
        log_blocked_attempt(command, reason)
        sys.stderr.write(f"\n🛑 [SECURITY HOOK BLOCKED] Destructive command intercepted!\n")
        sys.stderr.write(f"Command : {command}\n")
        sys.stderr.write(f"Reason  : {reason}\n")
        sys.stderr.write(f"Logged to: {get_log_path()}\n\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
