#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_tool_use.py — Claude Code PreToolUse hook that blocks destructive
bash commands before they are executed.

Installation (3 steps):
1. Copy this file to ~/.claude/hooks/pre_tool_use.py
2. Add the hook to your settings:
   ~/.claude/settings.json:
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             { "type": "command", "command": "python ~/.claude/hooks/pre_tool_use.py" }
           ]
         }
       ]
     }
   }
3. Restart Claude Code. Blocked commands are logged to ~/.claude/hooks/blocked.log

Protocol: reads one JSON object from stdin, writes a JSON decision to stdout.
Empty stdout (or no deny) means "allow".
"""

import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# (pattern, reason) — order matters, first match wins.
DANGEROUS_PATTERNS = [
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*(\s|$)", re.IGNORECASE), "rm -r deletes files recursively; use a safer alternative"),
    (re.compile(r"\bDROP\s+TABLE", re.IGNORECASE), "DROP TABLE destroys a database table irreversibly"),
    (re.compile(r"\bTRUNCATE\s+", re.IGNORECASE), "TRUNCATE wipes all rows from a table irreversibly"),
    (re.compile(r"\bgit\s+push\s+(-f|--force)", re.IGNORECASE), "force push overwrites remote history"),
    (re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE), "DELETE FROM without a WHERE clause would remove every row"),
    (re.compile(r"\bmysql\s+.*\s+-e\s+[\"']?DROP", re.IGNORECASE), "mysql DROP via -e flag is destructive"),
    (re.compile(r"\bdd\s+if=.*of=/dev/sd", re.IGNORECASE), "dd to a raw device can destroy the filesystem"),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Not a valid hook payload — do not block anything.
        print("")
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    if tool_name != "Bash" or not command:
        print("")
        return 0

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            # DELETE FROM with a WHERE clause is safe — allow it.
            if reason.startswith("DELETE FROM") and re.search(r"\bWHERE\b", command, re.IGNORECASE):
                continue
            cwd = payload.get("cwd") or os.getcwd()
            stamp = datetime.now().isoformat(timespec="seconds")
            try:
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[{stamp}] command: {command} | project: {cwd}\n")
            except OSError:
                pass
            decision = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked by pre_tool_use hook: {reason}. "
                        "If this is intentional, ask the user to run it manually with explicit confirmation."
                    ),
                }
            }
            print(json.dumps(decision, ensure_ascii=False))
            return 0

    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
