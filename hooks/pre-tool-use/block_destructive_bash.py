#!/usr/bin/env python3
"""Pre-tool-use hook for Claude Code to block destructive bash commands.

Repository: claude-builders-bounty/claude-builders-bounty
Issue: #3 ([BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands)

Blocked patterns:
  - `rm -rf` (and variations like `rm -fr`, `rm -r -f`, `--recursive --force`)
  - `DROP TABLE`
  - `git push --force` (or `git push -f`)
  - `TRUNCATE`
  - `DELETE FROM` without a `WHERE` clause
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Destructive pattern definitions
PATTERNS = [
    (
        "rm_rf",
        re.compile(
            r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*[rf][a-zA-Z]*|--recursive\s+--force|--force\s+--recursive|-r\s+-f|-f\s+-r)\b",
            re.IGNORECASE,
        ),
        "Recursive force removal ('rm -rf') is dangerous and blocked.",
    ),
    (
        "drop_table",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "SQL 'DROP TABLE' operation is destructive and blocked.",
    ),
    (
        "git_push_force",
        re.compile(r"\bgit\s+push\b.*?(?:--force|-f\b|--force-with-lease)", re.IGNORECASE),
        "Force pushing to git ('git push --force') can overwrite history and is blocked.",
    ),
    (
        "truncate",
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
        "SQL 'TRUNCATE' operation removes all rows and is blocked.",
    ),
    (
        "delete_without_where",
        re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE),
        "SQL 'DELETE FROM' without a WHERE clause will delete all table rows and is blocked.",
    ),
]


def check_command_safety(command: str) -> tuple[bool, str | None]:
    """Inspects command string. Returns (is_blocked, reason)."""
    if not command:
        return False, None

    for name, pattern, reason in PATTERNS:
        if name == "delete_without_where":
            if pattern.search(command):
                # Allow only if explicit WHERE clause is present
                if not re.search(r"\bWHERE\b", command, re.IGNORECASE):
                    return True, reason
        else:
            if pattern.search(command):
                return True, reason

    return False, None


def get_log_file_path() -> Path:
    """Returns log file path, allowing override via CLAUDE_HOOK_LOG_PATH."""
    override = os.environ.get("CLAUDE_HOOK_LOG_PATH")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(tool_name: str, command: str, reason: str) -> None:
    """Appends blocked command attempt to the audit log."""
    log_path = get_log_file_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [Tool: {tool_name}] REASON: {reason} | COMMAND: {command.strip()}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def evaluate_payload(tool_name: str, command: str) -> int:
    """Evaluates tool & command, logs if blocked, prints message to stderr. Returns exit code."""
    is_blocked, reason = check_command_safety(command)
    if is_blocked:
        log_blocked_attempt(tool_name, command, reason or "Destructive command pattern detected")
        sys.stderr.write(
            f"\n⛔ [Claude Code Hook] BLOCKED DESTRUCTIVE COMMAND\n"
            f"   Tool:    {tool_name}\n"
            f"   Command: {command.strip()}\n"
            f"   Reason:  {reason}\n"
            f"Operation aborted for repository safety.\n\n"
        )
        return 1
    return 0


def main() -> int:
    # 1. Check CLI arguments (e.g. --command "rm -rf /")
    if len(sys.argv) > 1:
        if "--command" in sys.argv:
            idx = sys.argv.index("--command")
            if idx + 1 < len(sys.argv):
                cmd = sys.argv[idx + 1]
                tool = "Bash"
                return evaluate_payload(tool, cmd)

    # 2. Parse stdin JSON payload from Claude Code pre-tool-use hook
    try:
        stdin_content = sys.stdin.read().strip()
        if not stdin_content:
            return 0
        data = json.loads(stdin_content)
        tool_name = data.get("tool") or data.get("name") or "Bash"
        tool_input = data.get("tool_input") or data.get("input") or {}
        command = ""
        if isinstance(tool_input, dict):
            command = tool_input.get("command") or tool_input.get("cmd") or ""
        elif isinstance(tool_input, str):
            command = tool_input

        if not command and "command" in data:
            command = data["command"]

        return evaluate_payload(tool_name, command)
    except json.JSONDecodeError:
        # If raw text is passed into stdin instead of JSON
        if stdin_content:
            return evaluate_payload("Bash", stdin_content)
        return 0
    except Exception as e:
        sys.stderr.write(f"Error parsing hook input: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
