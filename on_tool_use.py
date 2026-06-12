#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands.

Install: cp on_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bgit\s+push\s+--force\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.IGNORECASE),
]


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"is_blocked": False}))
        return

    tool_name = (payload.get("tool") or {}).get("name", "")
    tool_input = (payload.get("tool") or {}).get("input", {})

    command = ""
    if tool_name == "Bash":
        command = tool_input.get("command", "")
    elif tool_name in ("execute_command", "command"):
        command = tool_input.get("command", "")

    if not command:
        print(json.dumps({"is_blocked": False}))
        return

    for pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            project_path = os.getcwd()
            timestamp = datetime.now(timezone.utc).isoformat()

            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a") as f:
                f.write(f"[{timestamp}] BLOCKED | project={project_path} | cmd={command}\n")

            result = {
                "is_blocked": True,
                "message": (
                    f"[Blocked] Pattern '{pattern.pattern}' matched. "
                    f"This command was blocked by the bash guard hook. "
                    f"Logged to {LOG_FILE}"
                ),
            }
            print(json.dumps(result))
            return

    print(json.dumps({"is_blocked": False}))


if __name__ == "__main__":
    main()
