#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — blocks destructive Bash commands before they run.

Blocked patterns: rm -rf (and -fr/-Rf variants), DROP TABLE, git push --force
(and -f / --force-with-lease), TRUNCATE, DELETE FROM without a WHERE clause.

Reads the PreToolUse JSON event on stdin and prints a decision on stdout.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# (regex, human label). Order matters — first match wins.
DANGEROUS = [
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*\b", "recursive force delete (rm -rf/-fr)"),
    (r"\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*\b", "recursive force delete (rm -fr/-rf)"),
    (r"\bDROP\s+TABLE\b", "SQL DROP TABLE"),
    (r"\bgit\s+push\b[^\n]*(?:--force-with-lease|--force|-f\b)", "git force push"),
    (r"\bTRUNCATE\b", "SQL TRUNCATE"),
    (r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", "DELETE FROM without a WHERE clause"),
]


def log_block(command, label):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {label} | {os.getcwd()} | {command}\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    if data.get("tool_name") != "Bash":
        print(json.dumps({"decision": "allow"}))
        return

    command = (data.get("tool_input") or {}).get("command", "") or ""
    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    for pattern, label in DANGEROUS:
        if re.search(pattern, command, re.IGNORECASE):
            log_block(command, label)
            reason = (
                f"Blocked destructive command ({label}). "
                "This could destroy data irreversibly. If you are certain, run it "
                "manually outside Claude Code."
            )
            print(json.dumps({"decision": "block", "reason": reason}))
            return

    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
