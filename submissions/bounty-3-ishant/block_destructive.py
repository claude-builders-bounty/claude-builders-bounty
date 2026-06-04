#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Intercepts dangerous shell commands before Claude executes them and logs
every blocked attempt to ~/.claude/hooks/blocked.log.

Usage (configured via ~/.claude/settings.json):
  {
    "hooks": {
      "PreToolUse": [{
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive.py"}]
      }]
    }
  }
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")

# Each entry: (compiled_regex, human_readable_reason)
# Order matters — first match wins.
BLOCK_RULES: list[tuple[re.Pattern, str]] = [
    # rm -rf / rm -fr / rm -Rf etc.
    (re.compile(r"\brm\s+-[^\s]*[rR][^\s]*[fF]|-[^\s]*[fF][^\s]*[rR]", re.IGNORECASE),
     "rm -rf: recursive force deletion"),

    # git push --force / git push -f
    (re.compile(r"\bgit\s+push\b.*?(--force|-f)\b"),
     "git push --force: destructive remote history rewrite"),

    # SQL: DROP TABLE / DROP DATABASE / DROP SCHEMA
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "DROP TABLE/DATABASE/SCHEMA: permanent data destruction"),

    # SQL: TRUNCATE
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
     "TRUNCATE: removes all rows without WHERE"),

    # SQL: DELETE FROM without WHERE clause
    # Allowed:  DELETE FROM users WHERE id = 1
    # Blocked:  DELETE FROM users
    (re.compile(r"\bDELETE\s+FROM\b(?![\s\S]*?\bWHERE\b)", re.IGNORECASE),
     "DELETE FROM without WHERE: deletes every row in the table"),
]


# ── Helpers ─────────────────────────────────────────────────────────────────

def ensure_log_dir() -> None:
    os.makedirs(HOOKS_DIR, exist_ok=True)


def log_blocked(command: str, reason: str, project_path: str) -> None:
    ensure_log_dir()
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "reason": reason,
        "project_path": project_path,
        "command": command,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def block(command: str, reason: str, project_path: str) -> None:
    log_blocked(command, reason, project_path)
    output = {
        "decision": "block",
        "reason": (
            f"🚫 BLOCKED by safety hook: {reason}\n"
            f"Command: {command!r}\n"
            f"This attempt was logged to {LOG_FILE}.\n"
            "If you genuinely need to run this, ask the user to confirm "
            "and temporarily disable the hook in ~/.claude/settings.json."
        ),
    }
    print(json.dumps(output))
    sys.exit(2)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        payload: dict = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Malformed input — let Claude handle it normally.
        sys.exit(0)

    tool_name: str = payload.get("tool_name", "")
    tool_input: dict = payload.get("tool_input", {})

    # Only intercept the Bash tool.
    if tool_name != "Bash":
        sys.exit(0)

    command: str = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path: str = payload.get("project_path", os.getcwd())

    for pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            block(command, reason, project_path)
            return  # unreachable after sys.exit, but explicit for linters

    # No match — allow execution.
    sys.exit(0)


if __name__ == "__main__":
    main()
