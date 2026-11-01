#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook: Destructive Bash Command Blocker
Intercepts and blocks high-risk destructive commands before execution.
Compliant with Anthropic Claude Code Hooks Specification (~/.claude/hooks/).
"""

import sys
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Optional


# Destructive command detection patterns and human-readable explanations
# Detects:
# 1. rm -rf, rm -fr, rm -r -f, rm -f -r, rm --recursive --force, etc.
# 2. DROP TABLE / DROP DATABASE / DROP SCHEMA (case-insensitive, even inside quotes/subshells)
# 3. git push --force / -f / --force-with-lease
# 4. TRUNCATE TABLE / TRUNCATE
BLOCK_PATTERNS = [
    # 1. Recursive Force Delete (must have BOTH recursive AND force flags)
    (
        re.compile(
            r"\brm\s+(?:[^\n;&|]*\s)?(?:-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+.*--force|--force\s+.*--recursive|-[a-zA-Z]*r[a-zA-Z]*\s+.*-[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*\s+.*-[a-zA-Z]*r[a-zA-Z]*)\b",
            re.IGNORECASE,
        ),
        "Recursive force removal ('rm -rf') is prohibited to prevent irrecoverable data loss.",
    ),
    # 2. Database Drop (DROP TABLE / DROP DATABASE / DROP SCHEMA)
    (
        re.compile(r"(?:^|[\s;&|`$\(\'\"\\])drop\s+(?:table|database|schema)\b", re.IGNORECASE),
        "Database drop commands ('DROP TABLE / DATABASE / SCHEMA') are prohibited.",
    ),
    # 3. Git Force Push (git push --force, -f, --force-with-lease)
    (
        re.compile(
            r"\bgit\s+(?:-C\s+\S+\s+)?push\b(?=[^;\n|&]*\s(?:--force\b|-f\b|--force-with-lease\b|--force-if-includes\b))",
            re.IGNORECASE,
        ),
        "Git force pushing ('git push --force / -f / --force-with-lease') is prohibited to prevent destroying remote commit history.",
    ),
    # 4. Database Truncate (TRUNCATE / TRUNCATE TABLE)
    (
        re.compile(r"(?:^|[\s;&|`$\(\'\"\\])truncate\s+(?:table\s+)?[`\"']?[a-zA-Z0-9_]+[`\"']?", re.IGNORECASE),
        "Database truncation ('TRUNCATE TABLE') is prohibited.",
    ),
]


def check_delete_without_where(command: str) -> Optional[str]:
    """
    Checks for SQL 'DELETE FROM' statements lacking a WHERE clause.
    Allows safe statements such as: DELETE FROM users WHERE id = 123;
    Blocks dangerous statements such as: DELETE FROM users; or DELETE FROM users
    """
    # Find all DELETE FROM clauses
    delete_matches = re.finditer(r"(?i)\bdelete\s+from\s+([`\"']?[a-zA-Z0-9_.]+[`\"']?)([^;\n]*)", command)
    for m in delete_matches:
        table_name = m.group(1)
        rest_of_clause = m.group(2)
        # If clause does not contain 'where' keyword followed by a condition
        if not re.search(r"(?i)\bwhere\b", rest_of_clause):
            return f"Unrestricted 'DELETE FROM {table_name}' without a WHERE clause is prohibited."
    return None


def inspect_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Analyzes command string against destructive rules.
    Returns (is_blocked: bool, reason: Optional[str]).
    """
    if not command or not command.strip():
        return False, None

    # Check primary regex patterns
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return True, reason

    # Check DELETE without WHERE
    del_reason = check_delete_without_where(command)
    if del_reason:
        return True, del_reason

    return False, None


def get_log_file_path() -> Path:
    """Returns ~/.claude/hooks/blocked.log path, creating directory if missing."""
    home = Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or Path.home())
    hooks_dir = home / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "blocked.log"


def log_blocked_attempt(command: str, reason: str, project_path: str) -> None:
    """Logs the blocked attempt to ~/.claude/hooks/blocked.log."""
    log_file = get_log_file_path()
    iso_timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{iso_timestamp}] BLOCKED | Project: {project_path} | Command: {command} | Reason: {reason}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def parse_input() -> Tuple[str, str, str]:
    """
    Parses tool invocation from stdin (JSON format) or CLI arguments.
    Returns (tool_name, command, project_path).
    """
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    tool_name = "Bash"
    command = ""

    # Priority 1: Check stdin if input is piped
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    tool_name = payload.get("tool", tool_name)
                    tool_input = payload.get("tool_input", {})
                    if isinstance(tool_input, dict):
                        command = tool_input.get("command", "") or tool_input.get("cmd", "")
                    elif isinstance(tool_input, str):
                        command = tool_input
                    project_path = payload.get("project_path", project_path)
                except json.JSONDecodeError:
                    command = raw_input
        except Exception:
            pass

    # Priority 2: Check command line arguments if stdin had no command
    if not command and len(sys.argv) > 1:
        # Format: python block_destructive.py <tool_name> <command>
        if len(sys.argv) >= 3:
            tool_name = sys.argv[1]
            command = " ".join(sys.argv[2:])
        else:
            command = sys.argv[1]

    return tool_name, command, project_path


def main() -> int:
    tool_name, command, project_path = parse_input()

    # Only inspect Bash / shell execution tools
    if tool_name.lower() not in ("bash", "shell", "exec", "terminal", "sh"):
        return 0

    is_blocked, reason = inspect_command(command)

    if is_blocked and reason:
        log_blocked_attempt(command=command, reason=reason, project_path=project_path)

        message = (
            f"\n⛔ [SECURITY VIOLATION] Destructive command execution blocked.\n"
            f"   Command : {command}\n"
            f"   Reason  : {reason}\n"
            f"   Audit   : Logged to ~/.claude/hooks/blocked.log\n"
        )
        sys.stderr.write(message)
        # Exit code 2 tells Claude Code hook runner that tool execution is denied
        return 2

    # Safe command: Allow execution
    return 0


if __name__ == "__main__":
    sys.exit(main())
