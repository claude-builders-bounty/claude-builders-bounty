#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Destructive Command Blocker
Intercepts dangerous commands before execution, logs blocked attempts, and alerts Claude.
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

DESTRUCTIVE_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b", "Recursive forced deletion (rm -rf)"),
    (r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", "Recursive forced deletion (rm -fr)"),
    (r"\bDROP\s+TABLE\b", "SQL DROP TABLE operation"),
    (r"\bDROP\s+DATABASE\b", "SQL DROP DATABASE operation"),
    (r"\bgit\s+push\s+.*--force\b", "Destructive git push --force"),
    (r"\bgit\s+push\s+.*-f\b", "Destructive git push -f"),
    (r"\bTRUNCATE\s+TABLE?\b", "SQL TRUNCATE operation"),
    (r"\bDELETE\s+FROM\s+\w+\s*(?!WHERE\b)", "Unrestricted SQL DELETE without WHERE clause", re.IGNORECASE),
]

def get_log_file() -> Path:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "blocked.log"

def log_blocked(command: str, reason: str, project_path: str):
    log_file = get_log_file()
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] REASON: {reason} | PATH: {project_path} | CMD: {command}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)

def check_command(command: str, project_path: str = ".") -> bool:
    for item in DESTRUCTIVE_PATTERNS:
        pattern = item[0]
        reason = item[1]
        flags = item[2] if len(item) > 2 else re.IGNORECASE
        
        # Special check for DELETE FROM without WHERE
        if "DELETE" in reason:
            if re.search(r"\bDELETE\s+FROM\s+\w+", command, re.IGNORECASE) and not re.search(r"\bWHERE\b", command, re.IGNORECASE):
                log_blocked(command, reason, project_path)
                print(f"🛑 [BLOCKED BY SAFETY HOOK]: {reason}\nCommand: {command}\nThis action was intercepted to prevent irreversible data destruction.", file=sys.stderr)
                return False
        else:
            if re.search(pattern, command, flags):
                log_blocked(command, reason, project_path)
                print(f"🛑 [BLOCKED BY SAFETY HOOK]: {reason}\nCommand: {command}\nThis action was intercepted to prevent irreversible data destruction.", file=sys.stderr)
                return False
    return True

def main():
    project_path = os.getcwd()
    
    # Read payload from stdin (Claude Code JSON hook payload) or sys.argv
    command = ""
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    data = json.loads(raw_input)
                    command = data.get("tool_input", {}).get("command", "") or data.get("command", "")
                except Exception:
                    command = raw_input
        except Exception:
            pass

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if command:
        if not check_command(command, project_path):
            sys.exit(1)
            
    sys.exit(0)

if __name__ == "__main__":
    main()
