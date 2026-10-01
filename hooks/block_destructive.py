#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Installation (2 commands):
  mkdir -p ~/.claude/hooks
  cp block_destructive.py ~/.claude/hooks/pre-tool-use.py

Or add to ~/.claude/settings.json:
  {"hooks": {"PreToolUse": [{"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use.py"}]}}
"""
import json
import re
import sys
import logging
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.WARNING,
    format="%(asctime)s\t%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

# ── Destructive patterns ─────────────────────────────────────────────────────
# Each entry: (pattern, explanation)
BLOCKED_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Recursive force deletes
    (re.compile(r"rm\s+.*(-[rRfF]{1,4}|--recursive|--force).*(-[rRfF]{1,4}|--force|--recursive)", re.I),
     "Recursive force delete (rm -rf) can permanently destroy files."),

    # Force push (both --force and -f, also --force-with-lease)
    (re.compile(r"git\s+push\s+.*?(--force(?:-with-lease)?|-f)(?:\s|$)", re.I),
     "Force push rewrites remote history and can destroy others\' work."),

    # SQL: DROP (table, database, schema)
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.I),
     "DROP TABLE/DATABASE/SCHEMA permanently destroys data."),

    # SQL: TRUNCATE
    (re.compile(r"\bTRUNCATE\b", re.I),
     "TRUNCATE permanently removes all rows from a table."),

    # SQL: DELETE without WHERE
    (re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.I | re.S),
     "DELETE without WHERE removes every row in the table."),

    # chmod 777 recursively
    (re.compile(r"chmod\s+.*(-[rR]|--recursive).*777|chmod\s+777.*(-[rR]|--recursive)", re.I),
     "chmod -R 777 opens all permissions on every file — a major security risk."),

    # Fork bombs
    (re.compile(r":\s*\(\s*\)\s*\{.*:\|:&.*\}", re.S),
     "Fork bomb detected — this would crash the system."),

    # Disk/filesystem wipes
    (re.compile(r"mkfs\.|dd\s+.*of=\s*/dev/", re.I),
     "Filesystem format or disk wipe detected."),
]


def check_command(command: str) -> tuple[bool, str]:
    """Return (is_blocked, reason). Safe commands return (False, '')."""
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, ""


def block(command: str, reason: str, project_path: str) -> None:
    """Log the blocked attempt and exit with a deny response."""
    logging.warning("BLOCKED\t%s\tproject=%s\treason=%s", command[:200], project_path, reason)
    response = {
        "permissionDecision": "deny",
        "message": (
            f"🚫 **Blocked by pre-tool-use hook**\n\n"
            f"**Command:** `{command[:120]}`\n"
            f"**Reason:** {reason}\n\n"
            f"If this is intentional, disable the hook temporarily:\n"
            f"`mv ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py.disabled`"
        ),
    }
    print(json.dumps(response))
    sys.exit(0)  # exit 0 — we wrote a deny response, not an error


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Not a valid hook payload — pass through silently
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    project_path = payload.get("cwd", payload.get("workingDirectory", "unknown"))

    # Only inspect Bash tool calls
    if tool_name not in ("Bash", "bash", "execute_bash"):
        sys.exit(0)

    command = tool_input.get("command", "") or tool_input.get("cmd", "")
    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)
    if is_blocked:
        block(command, reason, project_path)

    # Safe — pass through
    sys.exit(0)


if __name__ == "__main__":
    main()
