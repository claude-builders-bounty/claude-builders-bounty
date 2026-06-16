#!/usr/bin/env python3
"""Pre-tool-use hook that blocks destructive bash commands in Claude Code.

Receives JSON on stdin with tool invocation context.
Exits code 0 to allow, code 2 to block (with reason in stderr).
Install: place in ~/.claude/hooks/ and add to .claude/settings.json.
"""
import json
import re
import sys
import os
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DESTRUCTIVE_PATTERNS = [
    (re.compile(r'\brm\s+(-rf|--recursive|--force|-r|-f)\b', re.IGNORECASE),
     "Recursive force delete (rm -rf) — use trash or careful rm instead"),
    (re.compile(r'\bdrop\s+table\b', re.IGNORECASE),
     "DROP TABLE — destructive schema change, use migrations instead"),
    (re.compile(r'\bgit\s+push\s+.*(--force|-f)\b', re.IGNORECASE),
     "Force push (git push --force) — use --force-with-lease if truly needed"),
    (re.compile(r'\btruncate\b', re.IGNORECASE),
     "TRUNCATE — destructive table clear, use DELETE or migrations"),
    (re.compile(r'\bdelete\s+from\b(?!.*\bwhere\b)', re.IGNORECASE),
     "DELETE FROM without WHERE clause — will remove ALL rows"),
]

def log_block(command, reason):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED | project={project} | reason={reason} | cmd={command}\n")


def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Not a valid event, silently allow
        sys.exit(0)

    tool_type = event.get("type", "")
    params = event.get("params", {})

    # Only intercept Bash tool calls
    if tool_type not in ("Bash", "bash"):
        sys.exit(0)

    command = params.get("command", "")
    if not command:
        sys.exit(0)

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            log_block(command, reason)
            message = (
                f"[destructive-commands-guard] BLOCKED: {reason}\n"
                f"  Command: {command}\n"
                f"  Logged to: {LOG_FILE}\n"
                f"  Override: not available — this hook is deterministic."
            )
            print(message, file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
