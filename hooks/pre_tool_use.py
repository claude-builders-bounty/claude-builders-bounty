#!/usr/bin/env python3
"""
Claude Code pre-tool-use Hook: Destructive Command Blocker
Placed in ~/.claude/hooks/pre_tool_use.py
Intercepts dangerous Bash/SQL commands (rm -rf, DROP TABLE, git push --force,
TRUNCATE, and DELETE FROM without a WHERE clause), logs blocked attempts to
~/.claude/hooks/blocked.log, and returns a clear rejection message to Claude.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force)\b", re.I),
     "Recursive forced deletion (rm -rf) is blocked to prevent irreversible filesystem loss."),
    (re.compile(r"\bDROP\s+TABLE\b", re.I),
     "SQL 'DROP TABLE' is blocked to prevent destructive schema deletion."),
    (re.compile(r"\bgit\s+push\s+.*(--force\b|-f\b)", re.I),
     "Force pushing (git push --force / -f) is blocked to protect remote commit history."),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w+", re.I),
     "SQL 'TRUNCATE' is blocked to prevent bulk table data loss."),
]

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\s+[\w."`]+(?P<tail>[^;]*)", re.I)

def check_command(cmd: str):
    for regex, reason in DESTRUCTIVE_PATTERNS:
        if regex.search(cmd):
            return reason
    for m in DELETE_FROM_RE.finditer(cmd):
        tail = m.group("tail") or ""
        if not re.search(r"\bWHERE\b", tail, re.I):
            return "Unbounded 'DELETE FROM' without a WHERE clause is blocked to prevent full-table deletion."
    return None

def log_blocked(cmd: str, project_path: str, reason: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] project={project_path} | cmd={json.dumps(cmd)} | reason={reason}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"command": raw}

    tool_input = payload.get("tool_input") or payload
    cmd = tool_input.get("command") or payload.get("command") or ""
    project_path = payload.get("cwd") or os.getcwd()

    reason = check_command(cmd)
    if reason:
        log_blocked(cmd, project_path, reason)
        response = {
            "decision": "block",
            "reason": f"🛑 [Security Hook Blocked Command]: {reason} (Logged to ~/.claude/hooks/blocked.log)"
        }
        print(json.dumps(response))
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
