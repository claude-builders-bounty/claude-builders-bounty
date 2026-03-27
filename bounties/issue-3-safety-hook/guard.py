#!/usr/bin/env python3
"""guard.py — Pre-tool-use hook that blocks destructive bash commands.

Python alternative to guard.sh with the same functionality but more precise
pattern matching and structured JSON output.

Input: JSON on stdin (Claude Code hook format)
Output: exit 0 (allow), exit 2 (block)
"""

import json
import sys
import re
import os
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────────────────────

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Patterns: (regex, severity, message)
# severity: "block" = always deny, "ask" = prompt user
PATTERNS = [
    # File system destruction
    (r"\brm\s+-rf\s+/", "block", "rm -rf / — recursive root deletion"),
    (r"\brm\s+-rf\s+", "ask", "rm -rf — recursive directory deletion"),
    (r"\brm\s+-r\s+/", "block", "rm -r / — recursive root deletion"),
    (r"> /dev/sd[a-z]", "block", "Write to block device — disk destruction"),
    (r"\bdd\s+.*of=/dev/", "block", "dd to device — disk overwrite"),
    (r"\bmkfs\.", "block", "mkfs — filesystem format"),
    (r"\bchmod\s+-R\s+777", "block", "chmod -R 777 — world-writable all files"),

    # SQL destruction
    (r"\bDROP\s+TABLE\b", "block", "DROP TABLE — irreversible table deletion"),
    (r"\bDROP\s+DATABASE\b", "block", "DROP DATABASE — irreversible database deletion"),
    (r"\bTRUNCATE\b", "block", "TRUNCATE — irreversible data wipe"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "block", "DELETE FROM without WHERE — deletes all rows"),

    # Git destruction
    (r"\bgit\s+push\b.*--force", "ask", "git push --force — rewrites remote history"),
    (r"\bgit\s+push\b.*-f\s", "ask", "git push -f — rewrites remote history"),
    (r"\bgit\s+reset\s+--hard", "ask", "git reset --hard — discards uncommitted changes"),
    (r"\bgit\s+clean\s+-f", "ask", "git clean -f — deletes untracked files"),
    (r"\bgit\s+branch\s+-D\b", "ask", "git branch -D — force deletes branch"),

    # Package destruction
    (r"\bnpm\s+publish\s+--force", "block", "npm publish --force — overwrites published package"),
    (r"\bdocker\s+system\s+prune\s+-a", "ask", "docker system prune -a — removes all unused data"),
]


def log_blocked(command: str, project_path: str, reason: str):
    """Append blocked command to log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {project_path} | {command} | {reason}\n")


def check_command(command: str) -> tuple:
    """Check command against all patterns.

    Returns: (matched: bool, severity: str, message: str)
    """
    for pattern, severity, message in PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, severity, message
    return False, "", ""


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    matched, severity, message = check_command(command)
    if not matched:
        sys.exit(0)

    project_path = data.get("cwd", "unknown")
    log_blocked(command, project_path, message)

    # Build structured output
    if severity == "block":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked: {message}. This is a destructive operation that cannot be undone.",
            }
        }
        print(f"[BLOCKED] {message}", file=sys.stderr)
        json.dump(output, sys.stderr)
        sys.exit(2)
    else:  # ask
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"Caution: {message}. Confirm this is intentional.",
            }
        }
        print(f"[CAUTION] {message}", file=sys.stderr)
        json.dump(output, sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
