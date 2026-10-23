#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that intercepts and blocks destructive bash commands.
Logs every blocked attempt to ~/.claude/hooks/blocked.log with timestamp, command, and project path.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

PATTERNS = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)\b", re.I),
     "Recursive forced file deletion (rm -rf) is destructive and blocked."),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.I),
     "SQL DROP TABLE / DATABASE is destructive and blocked."),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_.\[\]]+", re.I),
     "SQL TRUNCATE statement is destructive and blocked."),
    (re.compile(r"\bgit\s+push\s+([^;&|]*\s+)?(--force|-f|--force-with-lease)\b", re.I),
     "Force pushing (git push --force) can overwrite remote history and is blocked."),
    (re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.\[\]]+\s*(?:;|$)", re.I),
     "SQL DELETE FROM without a WHERE clause will wipe the entire table and is blocked."),
]

def has_unqualified_delete(cmd: str) -> bool:
    for match in re.finditer(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_.\[\]]+)([^;]*)", cmd, re.I):
        tail = match.group(2) or ""
        if not re.search(r"\bWHERE\b", tail, re.I):
            return True
    return False

def log_blocked(command: str, project_path: str, reason: str) -> None:
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] PROJECT={project_path} | COMMAND={command!r} | REASON={reason}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)

def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except Exception:
        return 0

    tool_name = payload.get("tool_name") or payload.get("tool") or ""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else ""

    if tool_name.lower() not in ("bash", "run_command", "") and not command:
        return 0
    if not command:
        return 0

    project_path = payload.get("cwd") or os.getcwd()

    for regex, reason in PATTERNS:
        if regex.search(command):
            log_blocked(command, project_path, reason)
            msg = f"BLOCKED by Claude Code Security Hook: {reason} (Attempted: {command})"
            print(json.dumps({"decision": "block", "reason": msg}))
            sys.stderr.write(msg + "\n")
            return 2

    if has_unqualified_delete(command):
        reason = "SQL DELETE FROM without a WHERE clause is blocked."
        log_blocked(command, project_path, reason)
        msg = f"BLOCKED by Claude Code Security Hook: {reason} (Attempted: {command})"
        print(json.dumps({"decision": "block", "reason": msg}))
        sys.stderr.write(msg + "\n")
        return 2

    return 0

if __name__ == "__main__":
    sys.exit(main())
