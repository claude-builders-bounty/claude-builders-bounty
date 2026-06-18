#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks dangerous bash commands.

Installation:
  mkdir -p ~/.claude/hooks
  cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
  chmod +x ~/.claude/hooks/pre_tool_use.py

Configure in ~/.claude/settings.json:
  {
    "hooks": {
      "PreToolUse": [
        { "matcher": "Bash", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use.py" }] }
      ]
    }
  }
"""

import json
import re
import sys
import logging
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

BLOCKED_PATTERNS: list[tuple[str, str]] = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\b", "rm -rf: recursive force delete"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE: destructive SQL"),
    (r"\bTRUNCATE\b", "TRUNCATE: destructive SQL"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE: wipes entire table"),
    (r"git\s+push\s+.*--force(?!-with-lease)", "git push --force: rewrites remote history"),
]


def check_command(command: str) -> tuple[bool, str]:
    """Return (is_blocked, reason). Case-insensitive match."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed input — let it through, don't crash the agent
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command: str = payload.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)

    if is_blocked:
        project_path = payload.get("cwd", "unknown")
        logging.info("BLOCKED | cmd=%r | reason=%s | project=%s", command[:200], reason, project_path)

        print(json.dumps({
            "decision": "block",
            "reason": (
                f"Blocked: {reason}.\n"
                f"Command: {command!r}\n"
                "If this is intentional, run the command manually in a terminal."
            ),
        }))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
