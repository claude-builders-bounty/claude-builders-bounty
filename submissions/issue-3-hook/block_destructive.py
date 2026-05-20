#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Logs every blocked attempt to ~/.claude/hooks/blocked.log.
"""

import json
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOK_DIR / "blocked.log"

# Each entry: (pattern, human-readable reason)
BLOCKED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b|\brm\s+--no-preserve-root\b'),
     "Recursive force delete (rm -rf) — permanently destroys files with no recovery path"),

    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
     "DROP TABLE — permanently destroys a database table and all its data"),

    (re.compile(r'\bTRUNCATE\b(?!\s+TRAILING|\s+LEADING|\s+BOTH)', re.IGNORECASE),
     "TRUNCATE — empties a table instantly with no transaction rollback in most engines"),

    (re.compile(r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', re.IGNORECASE | re.DOTALL),
     "DELETE FROM without WHERE — deletes every row in the table"),

    (re.compile(r'\bgit\s+push\s+(?:.*\s)?(?:--force|-f)\b'),
     "git push --force — overwrites remote history, potentially destroying teammates' work"),

    (re.compile(r'\bgit\s+reset\s+--hard\b'),
     "git reset --hard — permanently discards uncommitted changes"),

    (re.compile(r'\bchmod\s+-R\s+777\b|\bchmod\s+777\b'),
     "chmod 777 — grants world-writable permissions, a serious security risk"),

    (re.compile(r'>\s*/dev/null\s*2>&1.*&&\s*rm|rm.*>\s*/dev/null'),
     "Suspicious rm combined with output suppression — common pattern in destructive scripts"),

    (re.compile(r'\bdd\s+if=.*of=/dev/'),
     "dd writing to a device — can wipe disks or overwrite boot sectors"),

    (re.compile(r':\s*\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}'),
     "Fork bomb — will crash the system by exhausting process resources"),
]


def log_blocked(command: str, reason: str, project_path: str) -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project_path!r} | reason={reason!r} | command={command!r}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason). Checks all patterns."""
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, reason
    return False, ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse input, allow through — don't block on hook failure
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    # Only inspect Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = os.getcwd()

    is_blocked, reason = check_command(command)
    if not is_blocked:
        sys.exit(0)

    log_blocked(command, reason, project_path)

    message = (
        f"\n🚫 BLOCKED by safety hook\n"
        f"{'─' * 50}\n"
        f"Reason : {reason}\n"
        f"Command: {command[:200]}{'...' if len(command) > 200 else ''}\n"
        f"{'─' * 50}\n"
        f"If this was intentional, run the command directly in your terminal.\n"
        f"Blocked attempts are logged to: {LOG_FILE}\n"
    )

    print(message, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
