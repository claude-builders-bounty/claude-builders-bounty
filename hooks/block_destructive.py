#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Destructive Bash Commands
-----------------------------------------------------------
Intercepts dangerous commands before Claude executes them.
Compliant with Claude Code hook specifications (~/.claude/hooks/).

Blocked Patterns:
  - `rm -rf` (and variations like rm -fr, rm --recursive --force)
  - `DROP TABLE`
  - `git push --force` (including -f and +branch syntax)
  - `TRUNCATE` / `TRUNCATE TABLE`
  - `DELETE FROM` without a WHERE clause
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path


# Default log path inside user's Claude hooks directory
DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Regex rules for destructive commands
BLOCKED_PATTERNS = [
    (
        r"\brm\b.*?(-[a-zA-Z]*r[a-zA-Z]*f\b|-[a-zA-Z]*f[a-zA-Z]*r\b|(-r\b.*?-f\b|-f\b.*?-r\b)|--recursive.*?--force|--force.*?--recursive)",
        "rm -rf (recursive force deletion)",
    ),
    (
        r"\bDROP\s+TABLE\b",
        "DROP TABLE (destructive database drop)",
    ),
    (
        r"\bgit\s+push\s+.*(--force|-f|\+[a-zA-Z0-9_\-\/]+)",
        "git push --force (force push overwriting remote history)",
    ),
    (
        r"\bTRUNCATE(\s+TABLE)?\s+[a-zA-Z0-9_.\"`]",
        "TRUNCATE (bulk table wipe)",
    ),
    (
        r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.\"`]+(?!\s+WHERE\b)[^;]*($|;)",
        "DELETE FROM without WHERE clause (unbounded table deletion)",
    ),
]


def extract_command_from_payload(payload_str: str) -> str:
    """Extract the bash command string from Claude Code JSON payload or raw string."""
    payload_str = payload_str.strip()
    if not payload_str:
        return ""
    try:
        data = json.loads(payload_str)
        if isinstance(data, dict):
            # Format: {"tool_name": "Bash", "tool_input": {"command": "..."}}
            tool_input = data.get("tool_input", {})
            if isinstance(tool_input, dict) and "command" in tool_input:
                return str(tool_input["command"])
            # Format: {"command": "..."}
            if "command" in data:
                return str(data["command"])
    except json.JSONDecodeError:
        pass
    # If not valid JSON, treat raw string as the command
    return payload_str


def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any blocked destructive patterns.
    Returns (is_blocked, reason).
    """
    if not command:
        return False, ""

    # Check for DELETE FROM without WHERE (handling multi-line queries and case-insensitivity)
    # 1. Normalize whitespace
    normalized = " ".join(command.split())

    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            # Special check for DELETE FROM: ensure WHERE is truly absent
            if "DELETE FROM" in description.upper():
                # If "WHERE" exists in this delete statement, it's safe
                if re.search(r"\bDELETE\s+FROM\b.*\bWHERE\b", normalized, re.IGNORECASE):
                    continue
            return True, description

    return False, ""


def log_blocked_attempt(command: str, project_path: str, reason: str, log_file: Path | None = None) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log with timestamp, command, and project."""
    target_log = log_file or DEFAULT_LOG_PATH
    try:
        target_log.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] [BLOCKED] "
            f"Project: {project_path} | "
            f"Reason: {reason} | "
            f"Command: {command}\n"
        )
        with open(target_log, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[SafetyHook Warning] Failed to write to blocked.log: {e}\n")


def main() -> int:
    # 1. Read input payload from STDIN or CLI arguments
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    else:
        raw_input = sys.stdin.read()

    command = extract_command_from_payload(raw_input)
    if not command:
        return 0  # No command to inspect, allow

    # 2. Identify project path from environment variable or current directory
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # 3. Evaluate safety
    is_blocked, reason = check_command(command)

    if is_blocked:
        # 4. Log attempt
        log_blocked_attempt(command, project_path, reason)

        # 5. Output informative block message to stderr for Claude
        error_message = (
            f"\n⛔ [CLAUDE CODE SAFETY HOOK - EXECUTION BLOCKED]\n"
            f"Attempted Command: {command}\n"
            f"Blocked Pattern  : {reason}\n"
            f"Project Path     : {project_path}\n"
            f"Policy           : Destructive operations (rm -rf, DROP TABLE, git push --force,\n"
            f"                   TRUNCATE, DELETE without WHERE) are strictly prohibited.\n"
            f"Action Required  : Request explicit human confirmation or reformulate a non-destructive command.\n"
        )
        sys.stderr.write(error_message)
        return 2  # Exit code 2 tells Claude Code tool execution was aborted

    return 0


if __name__ == "__main__":
    sys.exit(main())
