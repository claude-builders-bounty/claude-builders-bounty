#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.

Usage (install into ~/.claude/hooks/pre_tool_use_block_destructive.py):
  1. Copy this file to ~/.claude/hooks/pre_tool_use_block_destructive.py
  2. Add to ~/.claude/settings.json:
     {
       "hooks": {
         "PreToolUse": [
           {
             "matcher": "Bash",
             "command": "python ~/.claude/hooks/pre_tool_use_block_destructive.py"
           }
         ]
       }
     }

Behavior:
  - Intercepts Bash tool calls before execution.
  - Blocks destructive commands: rm -rf, DROP TABLE, git push --force,
    TRUNCATE, DELETE FROM without a WHERE clause.
  - Logs every blocked attempt to ~/.claude/hooks/blocked.log
    (timestamp, attempted command, project path).
  - Prints a clear message to Claude explaining why the command was blocked.
  - Does not interfere with normal (non-destructive) bash commands.

Exit codes:
  0 = allow the command
  2 = block the command (Claude Code treats nonzero as block + shows stderr)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Destructive command patterns (matched case-insensitively).
DESTRUCTIVE_PATTERNS = [
    # rm with recursive + force flags (combined -rf/-fr or separate -r ... -f)
    (r"\brm\b.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*", "rm -rf / recursive delete"),
    (r"\brm\b.*(-r|-R|--recursive).*", "rm recursive delete"),
    # DROP TABLE (SQL)
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    # git push --force / --force-with-lease
    (r"\bgit\s+push\b.*(--force|-f|--force-with-lease)", "git push --force"),
    # TRUNCATE (SQL)
    (r"\bTRUNCATE\b", "TRUNCATE table"),
    # DELETE FROM ... without WHERE
    (r"\bDELETE\s+FROM\b(?!\s+.*\bWHERE\b)", "DELETE FROM without WHERE"),
]


def read_hook_input() -> dict:
    """Read the Claude Code hook JSON input from stdin."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def extract_command(hook_input: dict) -> str:
    """Extract the bash command from the hook input."""
    # Claude Code PreToolUse hook input shape:
    # {"tool": "Bash", "tool_input": {"command": "..."}, ...}
    tool_input = hook_input.get("tool_input", {}) if isinstance(hook_input, dict) else {}
    return tool_input.get("command", "")


def extract_project_path(hook_input: dict) -> str:
    """Extract the working/project directory from the hook input."""
    tool_input = hook_input.get("tool_input", {}) if isinstance(hook_input, dict) else {}
    return tool_input.get("cwd") or tool_input.get("working_directory") or os.getcwd()


def find_destructive(command: str):
    """Return (matched, reason) if command matches a destructive pattern."""
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked-attempt record to the log file."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    except OSError:
        pass
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} | BLOCKED | {reason} | cmd={command!r} | cwd={project_path}\n"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        # Best-effort logging; never block on a logging failure.
        pass


def main() -> int:
    hook_input = read_hook_input()
    command = extract_command(hook_input)
    project_path = extract_project_path(hook_input)

    if not command:
        # No command to inspect -> allow.
        return 0

    matched, reason = find_destructive(command)
    if matched:
        log_blocked(command, reason, project_path)
        msg = (
            "[pre-tool-use hook] BLOCKED destructive command: {reason}\n"
            "Command: {command}\n"
            "Project: {project_path}\n"
            "This attempt has been logged to ~/.claude/hooks/blocked.log\n"
            "If this is intentional, run the command directly outside Claude Code."
        ).format(reason=reason, command=command, project_path=project_path)
        # Write the rejection message to stderr so Claude Code surfaces it.
        sys.stderr.write(msg + "\n")
        return 2  # nonzero => block

    return 0  # allow


if __name__ == "__main__":
    sys.exit(main())
