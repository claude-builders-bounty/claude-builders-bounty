#!/usr/bin/env python3
"""pre-tool-use hook: blocks destructive bash commands.

Place at ~/.claude/hooks/pre-tool-use.py
Configure in Claude Code settings to run before tool execution.

Reads JSON from stdin with shape:
  {"tool_name": "Bash", "tool_input": {"command": "..."}}

Outputs JSON to stdout with shape:
  {"decision": "block", "reason": "..."}  -- block the command
  {}                                       -- allow the command
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Each entry: (compiled_regex, description)
DESTRUCTIVE_PATTERNS = [
    (re.compile(r"rm\s+(-\w*r\w*f\w*|--recursive)\s+", re.IGNORECASE), "rm -rf: recursively deletes files/directories"),
    (re.compile(r"rm\s+(-\w*f\w*r\w*|--recursive)\s+", re.IGNORECASE), "rm -rf: recursively deletes files/directories"),
    (re.compile(r"drop\s+table", re.IGNORECASE), "DROP TABLE: destroys database tables"),
    (re.compile(r"drop\s+database", re.IGNORECASE), "DROP DATABASE: destroys entire databases"),
    (re.compile(r"truncate\s+", re.IGNORECASE), "TRUNCATE: empties tables without logging"),
    (re.compile(r"git\s+push\s+.*--force", re.IGNORECASE), "git push --force: overwrites remote history"),
    (re.compile(r"git\s+push\s+.*\s-f\s", re.IGNORECASE), "git push -f: overwrites remote history"),
    (re.compile(r"git\s+push\s+.*\s-f$", re.IGNORECASE), "git push -f: overwrites remote history"),
    (re.compile(r"git\s+reset\s+--hard", re.IGNORECASE), "git reset --hard: discards all uncommitted changes"),
    (re.compile(r"git\s+clean\s+-\w*d\w*f", re.IGNORECASE), "git clean -df: removes untracked files/dirs"),
    (re.compile(r"chmod\s+-R\s+777", re.IGNORECASE), "chmod -R 777: makes everything world-writable"),
    (re.compile(r"chown\s+-R\s+", re.IGNORECASE), "chown -R: recursively changes ownership"),
    (re.compile(r"mkfs", re.IGNORECASE), "mkfs: formats a filesystem"),
    (re.compile(r"dd\s+.*of=/dev/", re.IGNORECASE), "dd to device: writes directly to disk device"),
    (re.compile(r">\s*/dev/sd", re.IGNORECASE), "redirect to disk device: overwrites raw disk"),
    (re.compile(r":\(\)\{.*\};:", re.IGNORECASE), "fork bomb: denial of service"),
    (re.compile(r"\bshutdown\b", re.IGNORECASE), "shutdown: powers off the machine"),
    (re.compile(r"\breboot\b", re.IGNORECASE), "reboot: restarts the machine"),
    (re.compile(r"\bhalt\b", re.IGNORECASE), "halt: stops the machine"),
    (re.compile(r"\bkillall\b", re.IGNORECASE), "killall: kills all processes by name"),
    (re.compile(r"pkill\s+-9", re.IGNORECASE), "pkill -9: force-kills processes"),
]

DELETE_WITHOUT_WHERE = re.compile(
    r"delete\s+from\s+\S+.*?(?:;|$)", re.IGNORECASE | re.DOTALL
)
HAS_WHERE = re.compile(r"where\s+", re.IGNORECASE)


def log_blocked(command: str, reason: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
        "reason": reason,
        "project_path": os.getcwd(),
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        sys.exit(0)

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    # Check destructive patterns
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            log_blocked(command, description)
            print(json.dumps({
                "decision": "block",
                "reason": f"Command blocked by pre-tool-use hook: {description}. "
                          "This destructive operation was intercepted to prevent data loss. "
                          "If this is intentional, ask the user to run the command manually."
            }))
            return

    # Check DELETE FROM without WHERE
    if DELETE_WITHOUT_WHERE.search(command) and not HAS_WHERE.search(command):
        log_blocked(command, "DELETE FROM without WHERE clause")
        print(json.dumps({
            "decision": "block",
            "reason": "Command blocked by pre-tool-use hook: DELETE FROM without WHERE clause. "
                      "This would delete all rows in the table. "
                      "If intentional, add a WHERE clause or ask the user to run it manually."
        }))
        return

    # Command is safe
    sys.exit(0)


if __name__ == "__main__":
    main()
