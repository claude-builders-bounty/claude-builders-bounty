#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive bash commands.

Install:
    mkdir -p ~/.claude/hooks
    cp hooks/block-destructive-commands.py ~/.claude/hooks/block-destructive-commands.py
    chmod +x ~/.claude/hooks/block-destructive-commands.py

Register in ~/.claude/settings.json:
    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Bash",
            "hooks": [
              {
                "type": "command",
                "command": "python3 ~/.claude/hooks/block-destructive-commands.py"
              }
            ]
          }
        ]
      }
    }
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns for destructive commands. Each entry is (name, compiled regex).
DESTRUCTIVE_PATTERNS = [
    ("rm -rf", re.compile(r"\brm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\b")),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b.*(--force\b|-f\b)")),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.IGNORECASE)),
]

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def find_violation(command: str):
    for name, pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return name

    if DELETE_FROM_RE.search(command) and not WHERE_RE.search(command):
        return "DELETE FROM without WHERE clause"

    return None


def log_blocked(command: str, reason: str, tool_name: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not command:
        return 0

    violation = find_violation(command)
    if violation is None:
        return 0

    log_blocked(command, violation, tool_name)

    output = {
        "decision": "block",
        "reason": (
            f"Blocked destructive command matching '{violation}'. "
            "This command was intercepted by the pre-tool-use safety hook."
        ),
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
