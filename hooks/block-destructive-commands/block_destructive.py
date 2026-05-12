#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

This hook intercepts dangerous bash commands before they are executed by Claude Code.
It blocks patterns like rm -rf, DROP TABLE, git push --force, TRUNCATE, and
DELETE FROM without a WHERE clause.

All blocked attempts are logged to ~/.claude/hooks/blocked.log.

Usage:
    Configure in ~/.claude/settings.json as a pre-tool-use hook.
    See README.md for installation instructions.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────────────────────
# Destructive command patterns
# ──────────────────────────────────────────────────────────────────────────────

DESTRUCTIVE_PATTERNS = [
    {
        "pattern": re.compile(r"\brm\s+.*-\w*r\w*f\w*\b|\brm\s+.*-\w*f\w*r\w*\b", re.IGNORECASE),
        "description": "rm -rf (recursive force delete)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b", re.IGNORECASE),
        "description": "DROP TABLE/DATABASE (destructive SQL)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+-f\b", re.IGNORECASE),
        "description": "git push --force (force push overwrites history)",
        "severity": "HIGH",
    },
    {
        "pattern": re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w+", re.IGNORECASE),
        "description": "TRUNCATE (removes all rows from table)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bDELETE\s+FROM\s+\w+(?!\s+WHERE)\s*;", re.IGNORECASE | re.DOTALL),
        "description": "DELETE FROM without WHERE clause (deletes all rows)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bDELETE\s+FROM\s+\w+\s*$", re.IGNORECASE | re.MULTILINE),
        "description": "DELETE FROM without WHERE clause (deletes all rows)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bmkfs\b", re.IGNORECASE),
        "description": "mkfs (format filesystem)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bdd\s+.*\bof=/dev/\b", re.IGNORECASE),
        "description": "dd writing to device (can destroy disk)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
        "description": "Redirect to raw device (data destruction)",
        "severity": "CRITICAL",
    },
    {
        "pattern": re.compile(r"\bchmod\s+.*-R\s+777\s+/\s*$", re.IGNORECASE),
        "description": "chmod -R 777 / (insecure permissions on root)",
        "severity": "HIGH",
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def log_blocked_command(command: str, reason: str, severity: str, project_path: str) -> None:
    """Log a blocked command attempt to ~/.claude/hooks/blocked.log."""
    os.makedirs(LOG_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    log_entry = {
        "timestamp": timestamp,
        "severity": severity,
        "attempted_command": command,
        "reason": reason,
        "project_path": project_path,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# Command checking
# ──────────────────────────────────────────────────────────────────────────────


def check_command(command: str) -> tuple[bool, str, str]:
    """
    Check if a command matches any destructive pattern.

    Returns:
        (is_blocked, description, severity)
    """
    for rule in DESTRUCTIVE_PATTERNS:
        if rule["pattern"].search(command):
            return True, rule["description"], rule["severity"]
    return False, "", ""


# ──────────────────────────────────────────────────────────────────────────────
# Main hook entrypoint
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """
    Read the hook input from stdin and decide whether to block the tool use.

    Claude Code pre-tool-use hooks receive JSON on stdin with the shape:
        {
            "tool_name": "Bash",
            "tool_input": { "command": "rm -rf /" }
        }

    To block execution, output JSON:
        { "decision": "block", "reason": "..." }

    To allow execution, output nothing or:
        { "decision": "allow" }
    """
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return

        hook_input = json.loads(raw_input)
    except (json.JSONDecodeError, KeyError):
        # If we can't parse the input, allow the command (fail-open)
        return

    tool_name = hook_input.get("tool_name", "")

    # Only inspect Bash / shell tool invocations
    if tool_name not in ("Bash", "bash", "shell", "terminal"):
        return

    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return

    is_blocked, description, severity = check_command(command)

    if is_blocked:
        project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        log_blocked_command(command, description, severity, project_path)

        result = {
            "decision": "block",
            "reason": (
                f"🚫 BLOCKED [{severity}]: {description}\n"
                f"Command: {command}\n"
                f"This command was blocked by the pre-tool-use safety hook because "
                f"it matches a known destructive pattern. If you believe this is a "
                f"false positive, please review the command carefully and consider "
                f"using a safer alternative.\n"
                f"Logged to: {LOG_FILE}"
            ),
        }
        print(json.dumps(result))
    # If not blocked, output nothing (implicit allow)


if __name__ == "__main__":
    main()
