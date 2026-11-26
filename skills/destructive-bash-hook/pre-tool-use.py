#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Reads hook JSON on stdin, decides allow/deny, logs blocked attempts to
~/.claude/hooks/blocked.log, and prints a clear message explaining the block.

Exit codes (Claude Code hook convention):
  0 = allow
  2 = block (stderr/stdout is shown to Claude)

Hook input (stdin JSON) commonly contains:
  {"tool_name":"Bash","tool_input":{"command":"..."},"cwd":"/path"}
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_PATH = os.path.join(LOG_DIR, "blocked.log")

# (regex, label, severity, reason)
RULES = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-[a-zA-Z]*r)\b",
     "rm -rf", "CRITICAL",
     "Recursive/forced delete can cause irreversible data loss."),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
     "DROP TABLE", "CRITICAL",
     "Dropping a table/database destroys schema and data permanently."),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+",
     "TRUNCATE", "CRITICAL",
     "TRUNCATE wipes all rows and cannot be rolled back in most engines."),
    (r"\bgit\s+push\b[^\n]*(\s--force\b|\s-f\b|--force-with-lease)",
     "git push --force", "CRITICAL",
     "Force-push can overwrite remote history and destroy teammates' work."),
    (r"\bDELETE\s+FROM\s+\w+",
     "DELETE FROM without WHERE", "CRITICAL",
     "DELETE without a WHERE clause removes every row in the table."),
]

# Refine: DELETE FROM is only dangerous without a WHERE clause.
DELETE_RE = re.compile(r"\bDELETE\s+FROM\s+\w+", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)

def classify(command: str):
    for pattern, label, severity, reason in RULES:
        if label == "DELETE FROM without WHERE":
            if DELETE_RE.search(command) and not WHERE_RE.search(command):
                return label, severity, reason
            continue
        if re.search(pattern, command, re.IGNORECASE):
            return label, severity, reason
    return None

def log_block(command, label, severity, cwd):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "pattern": label,
            "severity": severity,
            "project_path": cwd,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # never let logging break the hook

def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command") or data.get("command") or ""
    cwd = data.get("cwd") or os.getcwd()

    verdict = classify(command)
    if verdict:
        label, severity, reason = verdict
        log_block(command, label, severity, cwd)
        msg = (
            f"⛔ BLOCKED [{severity}]: {label}\n"
            f"Command: {command}\n"
            f"Reason: {reason}\n"
            f"Logged to: {LOG_PATH}\n"
            "This command was not executed. Use a safer alternative "
            "(e.g. add a WHERE clause, use `git push --force-with-lease` only "
            "after review, or delete specific files instead of rm -rf)."
        )
        print(msg, file=sys.stderr)
        sys.exit(2)

    # safe → allow silently
    sys.exit(0)

if __name__ == "__main__":
    main()
