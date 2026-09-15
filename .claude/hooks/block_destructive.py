#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Command Blocker
Intercepts hazardous shell commands and raw SQL operations before execution.
"""

import sys
import os
import re
import json
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def is_hazardous(command: str):
    cmd = " ".join(command.strip().split())
    
    # 1. rm checks
    if re.search(r"\brm\b", cmd):
        # Combined flags like -rf, -fr, -rfi, -frv
        if re.search(r"\brm\s+-[a-zA-Z0-9]*r[a-zA-Z0-9]*f[a-zA-Z0-9]*\b", cmd, re.I) or \
           re.search(r"\brm\s+-[a-zA-Z0-9]*f[a-zA-Z0-9]*r[a-zA-Z0-9]*\b", cmd, re.I):
            return "Recursive force deletion (`rm -rf`/`-fr`) is blocked."
        # Split flags or long flags: -r ... -f or --recursive ... --force
        has_r = re.search(r"(\s+-(?:[a-zA-Z0-9]*r[a-zA-Z0-9]*)\b|\s+--recursive\b)", cmd, re.I)
        has_f = re.search(r"(\s+-(?:[a-zA-Z0-9]*f[a-zA-Z0-9]*)\b|\s+--force\b)", cmd, re.I)
        if has_r and has_f:
            return "Recursive force deletion (`rm -r -f`) is blocked."

    # 2. git push force checks
    if re.search(r"\bgit\s+push\b", cmd):
        if re.search(r"(\s+--force\b|\s+-f\b|\s+--force-with-lease\b)", cmd):
            return "Force pushing to git remote (`git push --force`/`-f`) is blocked."

    # 3. SQL DROP checks
    if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", cmd, re.I):
        return "Database DROP operations (`DROP TABLE/DATABASE`) are blocked."

    # 4. SQL TRUNCATE checks
    if re.search(r"\bTRUNCATE(\s+TABLE)?\b", cmd, re.I):
        return "Database TRUNCATE operations are blocked."

    # 5. SQL DELETE without WHERE checks
    if re.search(r"\bDELETE\s+FROM\s+\w+\b", cmd, re.I):
        if not re.search(r"\bWHERE\b", cmd, re.I):
            return "Unbounded SQL DELETE without WHERE clause is blocked."

    return None

def log_blocked(command: str, cwd: str, reason: str):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "project_path": cwd,
            "attempted_command": command,
            "reason": reason
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        sys.stderr.write(f"[WARNING] Failed to write to {LOG_FILE}: {e}\n")

def main():
    cwd = os.getcwd()
    raw_input = sys.stdin.read()
    cmd = ""
    
    if raw_input.strip():
        try:
            payload = json.loads(raw_input)
            cmd = payload.get("command") or payload.get("input", {}).get("command", "")
        except json.JSONDecodeError:
            cmd = raw_input.strip()
    elif len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
    else:
        sys.exit(0)

    if cmd:
        reason = is_hazardous(cmd)
        if reason:
            log_blocked(cmd, cwd, reason)
            sys.stderr.write(f"\n[BLOCKED BY HOOK] {reason}\nAttempted Command: {cmd}\nProject Path: {cwd}\n")
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
