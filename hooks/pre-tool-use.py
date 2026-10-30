#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code: Intercepts & blocks destructive bash commands.
Format: Claude Code Hook (~/.claude/hooks/pre-tool-use.py)
"""
import sys
import os
import re
import json
from datetime import datetime

BLOCKED_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r", "Filesystem recursive forced wipe (rm -rf)"),
    (r"\bgit\s+push\s+.*(?:--force|-f)\b", "Git destructive remote rewrite (git push --force)"),
    (r"\bDROP\s+TABLE\b", "SQL destructive table removal (DROP TABLE)"),
    (r"\bTRUNCATE\b", "SQL table truncation (TRUNCATE)"),
    (r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)(?!.*\bWHERE\b)", "SQL unconstrained table deletion (DELETE FROM without WHERE)"),
]

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

def log_blocked(command: str, reason: str, cwd: str):
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] REASON: {reason} | CWD: {cwd} | CMD: {command}\n"
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def inspect_command(command: str, cwd: str):
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason, cwd)
            sys.stderr.write(
                f"\n❌ [SECURITY GUARD] Claude Code blocked a destructive command:\n"
                f"Reason: {reason}\n"
                f"Command: {command}\n"
                f"Audit logged to: {LOG_FILE}\n\n"
            )
            sys.exit(2)

def main():
    # Claude Code passes tool invocation context via stdin JSON or CLI arguments
    cwd = os.getcwd()
    cmd = ""
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            data = json.loads(raw)
            # Official PreToolUse payload; retain the legacy standalone formats.
            if data.get("tool_name") not in (None, "Bash"):
                return
            cwd = data.get("cwd") or cwd
            cmd = (data.get("tool_input", {}).get("command")
                   or data.get("command")
                   or data.get("input", {}).get("command", ""))
        except Exception:
            cmd = raw if "raw" in locals() else ""

    if cmd:
        inspect_command(cmd, cwd)
    sys.exit(0)

if __name__ == "__main__":
    main()
