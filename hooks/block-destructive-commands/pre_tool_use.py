#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Interceptor
Location: ~/.claude/hooks/pre-tool-use.py

Intercepts dangerous Bash execution requests within Claude Code and halts execution
before destructive operations can damage filesystems, git remotes, or databases.
"""

import sys
import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

# Paths
HOOKS_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOKS_DIR / "blocked.log"

# Forbidden patterns and reasons
FORBIDDEN_RULES = [
    {
        "id": "rm -rf",
        "pattern": re.compile(r"\brm\s+(-[a-zA-Z0-9]*r[a-zA-Z0-9]*f|-[a-zA-Z0-9]*f[a-zA-Z0-9]*r|--recursive\s+--force|--force\s+--recursive)\b", re.IGNORECASE),
        "reason": "Dangerous recursive force deletion detected"
    },
    {
        "id": "DROP TABLE",
        "pattern": re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\b", re.IGNORECASE),
        "reason": "Database destruction statement detected"
    },
    {
        "id": "git push --force",
        "pattern": re.compile(r"\bgit\s+push\b.*(\s+(-f|--force)\b|--force-with-lease=false|\+refs/)", re.IGNORECASE),
        "reason": "Destructive remote git branch overwrite detected"
    },
    {
        "id": "TRUNCATE",
        "pattern": re.compile(r"\bTRUNCATE(\s+TABLE)?\b", re.IGNORECASE),
        "reason": "Table truncation / bulk data purge statement detected"
    },
    {
        "id": "DELETE FROM without WHERE",
        "pattern": re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\".]+(?!\s+WHERE\b)", re.IGNORECASE),
        "check_custom": lambda cmd: bool(re.search(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\".]+", cmd, re.IGNORECASE)) and not bool(re.search(r"\bWHERE\b", cmd, re.IGNORECASE)),
        "reason": "Unbounded DELETE statement without WHERE clause detected"
    }
]

def extract_command(raw_input: str) -> str:
    raw = raw_input.strip()
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data.get("command", data.get("cmd", data.get("args", {}).get("command", raw)))
        except Exception:
            pass
    return raw

def evaluate_command(command: str):
    for rule in FORBIDDEN_RULES:
        if "check_custom" in rule:
            if rule["check_custom"](command):
                return rule["id"], rule["reason"]
        elif rule["pattern"].search(command):
            return rule["id"], rule["reason"]
    return None, None

def log_blocked(trigger: str, reason: str, command: str):
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    log_line = f"[{ts}] [BLOCKED:{trigger}] Reason: {reason} | Command: \"{command}\"\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def main():
    raw_input = ""
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read()

    command = extract_command(raw_input)
    if not command:
        sys.exit(0)

    trigger, reason = evaluate_command(command)
    if trigger:
        log_blocked(trigger, reason, command)
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write("🚨 [SECURITY HOOK BLOCKED] Command rejected by Claude Code pre-tool-use guard\n")
        sys.stderr.write("-" * 80 + "\n")
        sys.stderr.write(f"Trigger: {trigger}\n")
        sys.stderr.write(f"Reason:  {reason}\n")
        sys.stderr.write(f"Command: {command}\n")
        sys.stderr.write(f"Logged to: {LOG_FILE}\n")
        sys.stderr.write("=" * 80 + "\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
