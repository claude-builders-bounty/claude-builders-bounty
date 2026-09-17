#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook
Blocks destructive commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE)
and logs attempts to ~/.claude/hooks/blocked.log.
"""

import sys
import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

# Paths
LOG_FILE_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

def is_unconstrained_delete(cmd: str) -> bool:
    """
    Detects SQL DELETE FROM statements that do not contain a WHERE clause.
    Allows 'DELETE FROM table WHERE ...' while blocking 'DELETE FROM table' or 'DELETE FROM table;'.
    """
    # Look for DELETE FROM <identifier>
    matches = list(re.finditer(r'\bDELETE\s+FROM\s+([a-zA-Z0-9_"`\'\.]+)(.*)', cmd, re.IGNORECASE | re.DOTALL))
    if not matches:
        return False

    for m in matches:
        rest_of_query = m.group(2)
        # Strip string literals to prevent false matches inside strings
        cleaned = re.sub(r"'[^']*'|\"[^\"]*\"", "", rest_of_query)
        # Extract clause up to statement end or subquery / union boundary
        statement_part = re.split(r';|\)|(?:\b(?:UNION|INTERSECT|EXCEPT)\b)', cleaned, flags=re.IGNORECASE)[0]
        # If there is no WHERE keyword in the remainder of the query, it is unconstrained
        if not re.search(r'\bWHERE\b', statement_part, re.IGNORECASE):
            return True

    return False

# Prohibited destructive command patterns
DESTRUCTIVE_RULES = [
    {
        "name": "Recursive Force Delete (rm -rf)",
        "pattern": re.compile(r'\brm\s+(?:-[a-zA-Z0-9]*[rf][a-zA-Z0-9]*[rf][a-zA-Z0-9]*|--recursive\s+--force|--force\s+--recursive|-r\s+-f|-f\s+-r)\b', re.IGNORECASE),
        "reason": "Destructive filesystem deletion ('rm -rf' / recursive force remove). Use specific path removals with explicit confirmation."
    },
    {
        "name": "Drop Database Table (DROP TABLE)",
        "pattern": re.compile(r'\bDROP\s+TABLE(?:\s+IF\s+EXISTS)?\s+[\w"`\'\.]+', re.IGNORECASE),
        "reason": "Irreversible database modification ('DROP TABLE'). Schema drops must be performed manually."
    },
    {
        "name": "Force Push Git Branch (git push --force)",
        "pattern": re.compile(r'\bgit\s+push\s+(?:[^\n;&|]*\s+)?(?:--force|-f\b|\+[a-zA-Z0-9_\-\/]+)', re.IGNORECASE),
        "reason": "Destructive remote git history rewrite ('git push --force' or '-f'). Use safe pushes or pull rebase."
    },
    {
        "name": "Truncate Database Table (TRUNCATE)",
        "pattern": re.compile(r'\bTRUNCATE(?:\s+TABLE)?\s+[\w"`\'\.]+', re.IGNORECASE),
        "reason": "Complete database table wipe ('TRUNCATE TABLE'). Mass record removal is restricted."
    },
    {
        "name": "Unconstrained Delete (DELETE FROM without WHERE)",
        "custom_check": is_unconstrained_delete,
        "reason": "Unconstrained table deletion ('DELETE FROM' without a WHERE clause). Specify WHERE conditions to limit scope."
    }
]

def check_command(command: str) -> tuple[bool, str | None, str | None]:
    """
    Checks if a command matches any destructive rules.
    Returns: (is_blocked, rule_name, reason)
    """
    for rule in DESTRUCTIVE_RULES:
        if "custom_check" in rule:
            if rule["custom_check"](command):
                return True, rule["name"], rule["reason"]
        elif "pattern" in rule and rule["pattern"].search(command):
            return True, rule["name"], rule["reason"]
    return False, None, None

def log_blocked_attempt(command: str, project_path: str, reason: str):
    """Logs the blocked command attempt to ~/.claude/hooks/blocked.log"""
    try:
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        log_entry = f"[{timestamp}] BLOCKED | Path: {project_path} | Command: {command.strip()} | Reason: {reason}\n"
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to blocked.log: {e}\n")

def parse_input() -> tuple[str, str]:
    """
    Extracts command and project directory from stdin JSON or CLI arguments.
    Supports Claude Code hook protocol and standalone CLI executions.
    """
    project_path = os.getcwd()
    command = ""

    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        return command, project_path

    # Read from stdin if available
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    # Standard Claude Code Hook Payload
                    if isinstance(payload, dict):
                        project_path = payload.get("cwd", payload.get("working_directory", os.getcwd()))
                        
                        # Extract command from tool_input or arguments
                        tool_input = payload.get("tool_input", payload.get("arguments", {}))
                        if isinstance(tool_input, dict):
                            command = tool_input.get("command", tool_input.get("cmd", ""))
                        elif isinstance(tool_input, str):
                            command = tool_input
                        elif "command" in payload:
                            command = payload["command"]
                except json.JSONDecodeError:
                    command = raw_input
        except Exception:
            pass

    return command, project_path

def main():
    command, project_path = parse_input()

    if not command:
        # No command to inspect, allow pass-through
        sys.exit(0)

    is_blocked, rule_name, reason = check_command(command)

    if is_blocked:
        log_blocked_attempt(command, project_path, reason)
        
        # Output clear, actionable feedback to Claude Code
        error_message = (
            f"\n🛑 [SECURITY HOOK BLOCKED]\n"
            f"Rule Triggered: {rule_name}\n"
            f"Blocked Command: {command}\n"
            f"Reason: {reason}\n"
            f"Audit Log: Logged to {LOG_FILE_PATH}\n"
            f"Action Required: Use safe, targeted commands with explicit confirmation.\n"
        )
        sys.stderr.write(error_message)
        # Exit with status code 2 to indicate hook rejection to Claude Code
        sys.exit(2)

    # Allowed command
    sys.exit(0)

if __name__ == "__main__":
    main()
