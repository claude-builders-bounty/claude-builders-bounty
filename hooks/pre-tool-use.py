#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks dangerous bash commands.

Blocked patterns:
  - rm -rf                        (recursive force delete)
  - DROP TABLE                    (destructive database operation)
  - git push --force              (overwrites remote history)
  - TRUNCATE                      (destructive database operation)
  - DELETE FROM without WHERE     (unconditional row deletion)

Every blocked attempt is logged to ~/.claude/hooks/blocked.log with
timestamp, attempted command, and project path.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def is_blocked(command: str) -> tuple[bool, str]:
    """Return (True, reason) if the command matches a blocked pattern."""
    cmd = command.strip()

    if re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f', cmd, re.IGNORECASE):
        return True, "rm -rf (recursive force delete)"

    if re.search(r'\bDROP\s+TABLE\b', cmd, re.IGNORECASE):
        return True, "DROP TABLE (destructive database operation)"

    if re.search(r'\bgit\s+push\s+--force\b', cmd, re.IGNORECASE):
        return True, "git push --force (overwrites remote history)"

    if re.search(r'\bTRUNCATE\b', cmd, re.IGNORECASE):
        return True, "TRUNCATE (destructive database operation)"

    if (re.search(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE)
            and not re.search(r'\bWHERE\b', cmd, re.IGNORECASE)):
        return True, "DELETE FROM without WHERE clause (unconditional row deletion)"

    return False, ""


def log_blocked(command: str, project_path: str, reason: str):
    """Append a blocked attempt to ~/.claude/hooks/blocked.log."""
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "blocked.log"
    timestamp = datetime.now().isoformat()
    with open(log_path, "a") as f:
        f.write(f"{timestamp} | {command} | {project_path} | {reason}\n")


def main():
    # Read JSON payload from stdin (Claude Code hook contract)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Don't block on unparseable input

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Only inspect Bash commands — let everything else pass through
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    project_path = payload.get("cwd", os.getcwd())

    blocked, reason = is_blocked(command)
    if blocked:
        log_blocked(command, project_path, reason)
        # Output JSON with block reason — Claude Code shows this to the model
        response = {
            "action": "block",
            "reason": (
                f"🚫 BLOCKED: {reason}. "
                f"This command was blocked by a safety hook. "
                f"Please use a safer alternative or ask the user to run it manually."
            ),
        }
        print(json.dumps(response))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
