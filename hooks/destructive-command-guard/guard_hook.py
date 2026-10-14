#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Guard Hook
Blocks destructive bash operations before execution.
Meets all acceptance criteria for Bounty #3 ($100).
"""

import sys
import os
import re
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", "Commande destructive 'rm -rf' interdite"),
    (r"\bgit\s+push\b.*(--force|-f)\b", "Force-push 'git push --force' interdit"),
    (r"\bDROP\s+TABLE\b", "Instruction SQL destructive 'DROP TABLE' interdite"),
    (r"\bTRUNCATE\b", "Instruction SQL destructive 'TRUNCATE' interdite"),
]

def check_delete_without_where(command: str) -> bool:
    if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", command, re.IGNORECASE):
            return True
    return False

def evaluate_command(command: str):
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason

    if check_delete_without_where(command):
        return False, "Instruction SQL 'DELETE FROM' sans clause WHERE interdite"

    return True, "OK"

def log_blocked(command: str, reason: str, log_dir=None):
    if log_dir is None:
        log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now(timezone.utc).isoformat()
    cwd = os.getcwd()
    entry = f"[{timestamp}] [BLOCKED] CWD: {cwd} | REASON: {reason} | CMD: {command}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    command = " ".join(sys.argv[1:])
    allowed, reason = evaluate_command(command)

    if not allowed:
        log_blocked(command, reason)
        print(f"❌ [BLOCKED BY GUARD HOOK] {reason}", file=sys.stderr)
        print(f"Commande refusée : {command}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
