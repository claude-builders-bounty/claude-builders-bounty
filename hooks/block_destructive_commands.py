#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands.

Intercepts and blocks dangerous bash commands before execution in Claude Code.
Blocked patterns:
- rm -rf (and variants)
- DROP TABLE
- git push --force (and -f)
- TRUNCATE
- DELETE FROM without a WHERE clause
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKED_PATTERNS = [
    (
        r'\brm\s+.*-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b|\brm\s+-[a-zA-Z]*r\s+-[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f\s+-[a-zA-Z]*r\b',
        "Destructive file removal pattern detected ('rm -rf').",
    ),
    (
        r'\bDROP\s+TABLE\b',
        "Destructive SQL operation detected ('DROP TABLE').",
    ),
    (
        r'\bgit\s+push\b.*?(?:--(?:force|force-with-lease)|-f\b)',
        "Destructive Git operation detected ('git push --force').",
    ),
    (
        r'\bTRUNCATE\b',
        "Destructive SQL operation detected ('TRUNCATE').",
    ),
]

# Safe context prefixes where keyword occurrences (like in commit messages or docs) are non-executable
SAFE_PREFIX_PATTERNS = [
    r'^\s*git\s+(?:commit|log|diff|show|status)\b',
    r'^\s*grep\b',
    r'^\s*cat\b',
]


def is_destructive_command(command: str) -> tuple[bool, str]:
    """Check if command matches any prohibited destructive pattern."""
    if not command or not command.strip():
        return False, ""

    cmd_str = command.strip()

    # Allow safe read-only / VCS commands containing keywords in strings/messages
    for safe_pattern in SAFE_PREFIX_PATTERNS:
        if re.search(safe_pattern, cmd_str, re.IGNORECASE) and not re.search(r'\||;', cmd_str):
            # Check rm -rf even in safe prefixes just in case
            if not re.search(r'\brm\s+.*-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b', cmd_str, re.IGNORECASE):
                return False, ""

    # Check regex pattern list
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_str, re.IGNORECASE):
            return True, reason

    # Check DELETE FROM without WHERE clause
    if re.search(r'\bDELETE\s+FROM\b', cmd_str, re.IGNORECASE):
        if not re.search(r'\bWHERE\b', cmd_str, re.IGNORECASE):
            return True, "Destructive SQL operation detected ('DELETE FROM' without 'WHERE' clause)."

    return False, ""


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log with timestamp, command, and project path."""
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_file = hooks_dir / "blocked.log"

    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = (
        f"[{timestamp}] PROJECT: {project_path} | "
        f"REASON: {reason} | "
        f"COMMAND: {command}\n"
    )

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def main() -> None:
    command = ""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")

    # Read tool payload from stdin if available
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                try:
                    payload = json.loads(stdin_data)
                    if isinstance(payload, dict):
                        tool_name = payload.get("tool_name") or payload.get("tool") or tool_name
                        project_path = payload.get("cwd") or payload.get("project_path") or project_path
                        tool_input = payload.get("tool_input") or payload.get("input") or {}
                        if isinstance(tool_input, dict):
                            command = tool_input.get("command") or tool_input.get("cmd") or ""
                        elif isinstance(tool_input, str):
                            command = tool_input
                except json.JSONDecodeError:
                    command = stdin_data.strip()
        except Exception:
            pass

    # Fallback to CLI arguments if stdin is empty
    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    # Ignore non-bash tools if tool name is explicitly specified
    if tool_name and tool_name.lower() not in ("bash", "terminal", "executecommand", "sh"):
        sys.exit(0)

    blocked, reason = is_destructive_command(command)
    if blocked:
        log_blocked_attempt(command, project_path, reason)
        error_msg = (
            f"\n\033[1;31m[BLOCKED BY CLAUDE CODE HOOK]\033[0m\n"
            f"Command blocked for security reasons:\n"
            f"  Command: {command}\n"
            f"  Reason:  {reason}\n"
            f"  Log:     ~/.claude/hooks/blocked.log\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
