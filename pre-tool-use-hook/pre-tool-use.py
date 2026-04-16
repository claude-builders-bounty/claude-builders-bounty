#!/usr/bin/env python3
"""
pre-tool-use hook: blocks destructive bash commands
Claude Code hook format: ~/.claude/hooks/pre-tool-use
Python alternative — more robust JSON parsing than bash grep approach
"""
import sys
import json
import re
import os
from datetime import datetime

BLOCKED_LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    (re.compile(r'rm\s+-rf\s+'), "rm -rf — recursive force delete"),
    (re.compile(r'rm\s+-r\s+/\w+'), "rm -r on root-level dir"),
    (re.compile(r'rm\s+-f\s+/\w+'), "rm -f on root-level file"),
    (re.compile(r'dd\s+if=.*of=/'), "dd disk overwrite — catastrophic"),
    (re.compile(r'mkfs'), "mkfs — filesystem destruction"),
    (re.compile(r'fdisk\s+-[ld]'), "fdisk — partition table modification"),
    (re.compile(r'git\s+push\s+--force'), "git push --force — history rewrite"),
    (re.compile(r'git\s+push\s+-f\b'), "git push -f — forced push"),
    (re.compile(r':\(\)\s*:\s*\|:\s*&\s*;'), "fork bomb"),
]

SQL_DELETE_NO_WHERE = re.compile(
    r'\bDELETE\s+FROM\s+[a-zA-Z_0-9.]+\s*(?:WHERE|$|\;|--)',
    re.IGNORECASE
)
SQL_DELETE_BLOCK = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)
SQL_TRUNCATE = re.compile(r'\bTRUNCATE\s+TABLE\b', re.IGNORECASE)
SQL_DROP = re.compile(r'\bDROP\s+(?:TABLE|DATABASE)\b', re.IGNORECASE)


def parse_input():
    """Parse Claude Code hook JSON from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return None


def get_command_from_input(data):
    """Extract command string from various tool inputs."""
    if not data:
        return None

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Bash / Terminal
    if tool_name in ("Bash", "Terminal"):
        return tool_input.get("command", "")

    # Read / Write file tools — block if writing to critical paths
    if tool_name in ("Write", "Edit"):
        # Could check file paths here if needed
        return None

    return None


def check_dangerous(command: str) -> tuple[bool, str]:
    """Check if command matches any dangerous pattern. Returns (blocked, reason)."""
    if not command:
        return False, ""

    cmd_upper = command.upper()

    # Check SQL destructive commands
    if SQL_DROP.search(cmd_upper):
        match = SQL_DROP.search(cmd_upper)
        return True, f"DROP {match.group(1)} — destructive SQL command"

    if SQL_TRUNCATE.search(cmd_upper):
        return True, "TRUNCATE — entire table deletion"

    if SQL_DELETE_BLOCK.search(cmd_upper) and not SQL_DELETE_NO_WHERE.search(command):
        return True, "DELETE FROM without WHERE clause — data loss risk"

    # Check bash patterns
    for pattern, description in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True, description

    return False, ""


def main():
    data = parse_input()
    if not data:
        sys.exit(0)  # Allow on parse failure

    tool_name = data.get("tool_name", "")
    command = get_command_from_input(data)

    # Only check bash/terminal commands
    if tool_name not in ("Bash", "Terminal"):
        sys.exit(0)

    if not command:
        sys.exit(0)

    blocked, reason = check_dangerous(command)

    if blocked:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_path = os.getcwd() or "unknown"
        log_entry = f"[{timestamp}] BLOCKED: {command[:200]} | Reason: {reason} | Path: {project_path}\n"

        os.makedirs(os.path.dirname(BLOCKED_LOG), exist_ok=True)
        with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Print blocking message to stderr — Claude reads this
        print(f"\n⛔ BLOCKED: {reason}", file=sys.stderr)
        print(f"   Command: {command[:200]}", file=sys.stderr)
        print(file=sys.stderr)
        print("This command was blocked by your pre-tool-use security hook.", file=sys.stderr)
        print("Disable the hook temporarily if you need to run this.", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
