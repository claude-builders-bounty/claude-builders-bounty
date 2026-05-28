#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import sys
import os
import re
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

BLOCKED_PATTERNS = [
    (r'\brm\s+-[a-z]*r[a-z]*f|rm\s+-[a-z]*f[a-z]*r', "rm -rf: recursive force delete"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE: destroys database table"),
    (r'\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b', "git push --force: overwrites remote history"),
    (r'\bTRUNCATE\b', "TRUNCATE: wipes entire table"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)', "DELETE FROM without WHERE: deletes all rows"),
]

def log_blocked(command: str, reason: str) -> None:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    project = os.getcwd()
    ts = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] BLOCKED | project={project} | reason={reason} | cmd={command}\n")

def check_command(command: str) -> tuple[bool, str]:
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name not in ("Bash", "bash"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    blocked, reason = check_command(command)
    if not blocked:
        sys.exit(0)

    log_blocked(command, reason)

    response = {
        "decision": "block",
        "reason": (
            f"BLOCKED: {reason}\n"
            f"Command: {command!r}\n"
            f"This command was intercepted by the pre-tool-use safety hook because it matches "
            f"a destructive pattern. If you genuinely need to run this, the user must approve it "
            f"explicitly. Blocked attempt logged to: {LOG_FILE}"
        )
    }
    print(json.dumps(response))
    sys.exit(0)

if __name__ == "__main__":
    main()
