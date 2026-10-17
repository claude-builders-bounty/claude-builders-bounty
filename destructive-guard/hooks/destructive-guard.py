#!/usr/bin/env python3
"""destructive-guard — Claude Code PreToolUse hook.

Blocks dangerous bash commands before execution. Reads the hook event JSON on
stdin, inspects tool_input.command, and exits non-zero (deny) with a clear
message when the command matches a destructive pattern. Every blocked attempt
is appended to ~/.claude/hooks/blocked.log with timestamp, command, project.

Install: see README.md (2 commands).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG = os.path.expanduser(os.path.join("~", ".claude", "hooks", "blocked.log"))

# (name, regex, human explanation). Regexes run on the raw command string.
PATTERNS = [
    ("rm -rf", r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+",
     "recursive+force delete"),
    ("DROP TABLE", r"\bDROP\s+TABLE\b",
     "drops a database table irreversibly"),
    ("TRUNCATE", r"\bTRUNCATE\s+(TABLE\s+)?\w",
     "deletes every row without row-level audit"),
    ("DELETE no WHERE", r"\bDELETE\s+FROM\s+\w+\s*;?\s*$",
     "deletes every row in the table (no WHERE clause)"),
    ("git push --force", r"\bgit\s+push\b[^|;]*(--force\b|-f\b)",
     "rewrites remote history; can destroy others' work"),
    ("git reset --hard remote", r"\bgit\s+reset\s+--hard\b[^|;]*\b(origin|upstream)/",
     "discards local commits to match a remote"),
    ("mkfs / dd to device", r"\b(mkfs\b|dd\b[^|;]*\bof=/dev/)",
     "writes raw data to a block device"),
    ("fork bomb / :(){", r":\(\)\s*\{",
     "process fork bomb"),
]


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return  # malformed event — allow rather than break the session

    if event.get("tool_name") != "Bash":
        return
    cmd = (event.get("tool_input") or {}).get("command") or ""
    cwd = event.get("cwd") or os.getcwd()

    for name, pat, why in PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now(timezone.utc).isoformat()}\t{cwd}\t{name}\t{cmd}\n"
                )
            sys.stderr.write(
                f"BLOCKED by destructive-guard ({name}: {why}).\n"
                f"Command: {cmd}\n"
                f"If this is genuinely intended, run it yourself in a terminal — "
                f"this hook only blocks agent-initiated commands."
            )
            sys.exit(2)  # exit 2 = deny the tool call, stderr shown to Claude

    sys.exit(0)  # allow


if __name__ == "__main__":
    main()
