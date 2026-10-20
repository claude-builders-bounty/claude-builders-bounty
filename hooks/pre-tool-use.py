#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Intercepts dangerous bash commands before execution and logs security violations.
"""

import sys
import re
import os
import json
from datetime import datetime

BLOCKED_PATTERNS = [
    # Recursive unconstrained deletions
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b", "Recursive forced deletion (`rm -rf`)"),
    (r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b", "Recursive forced deletion (`rm -fr`)"),
    
    # Destructive SQL queries
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\b", "Destructive SQL DROP statement"),
    (r"\bTRUNCATE(\s+TABLE)?\b", "Destructive SQL TRUNCATE statement"),
    (r"\bDELETE\s+FROM\s+([a-zA-Z0-9_\"`]+)(?![\s\S]*\bWHERE\b)", "Unbounded SQL DELETE without a WHERE clause"),
    
    # Git destructive commands
    (r"\bgit\s+push\s+.*(--force|-f)\b", "Destructive git push force (`--force` / `-f`)"),
    (r"\bgit\s+reset\s+--hard\s+origin/", "Destructive git hard reset against remote"),
    
    # Filesystem and disk wipe hazards
    (r"\bmkfs(\.[a-zA-Z0-9]+)?\b", "Direct disk format command (`mkfs`)"),
    (r"\bdd\s+if=.*of=(/dev/|/dev/sd|/dev/nvme)", "Raw block device overwrite (`dd`)"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb denial of service")
]

def get_log_path():
    hooks_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    return os.path.join(hooks_dir, "blocked.log")

def log_blocked(command: str, reason: str, project_dir: str):
    log_path = get_log_path()
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] REASON: {reason} | DIR: {project_dir} | CMD: {command.strip()}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def check_command(command: str) -> tuple[bool, str]:
    clean_cmd = command.strip()
    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, clean_cmd, re.IGNORECASE):
            return True, description
    return False, ""

def main():
    # Supports reading from command-line arguments or stdin (JSON or string)
    command = ""
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        # Check standard input
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                # Check if Claude Code passed JSON payload { tool: "bash", command: "..." }
                if stdin_data.startswith("{") and stdin_data.endswith("}"):
                    try:
                        payload = json.loads(stdin_data)
                        command = payload.get("command") or payload.get("input", {}).get("command", "")
                    except Exception:
                        command = stdin_data
                else:
                    command = stdin_data
        except Exception:
            pass

    if not command:
        # No command to inspect, allow execution
        sys.exit(0)

    is_blocked, reason = check_command(command)
    if is_blocked:
        project_dir = os.getcwd()
        log_blocked(command, reason, project_dir)
        
        # Display explicit, professional alert to Claude and exit with non-zero
        sys.stderr.write("\n" + "="*70 + "\n")
        sys.stderr.write("🛑 [SECURITY BLOCKED]: Dangerous Command Intercepted by Claude Hook\n")
        sys.stderr.write(f"Reason:  {reason}\n")
        sys.stderr.write(f"Command: {command.strip()}\n")
        sys.stderr.write(f"Logged to: ~/.claude/hooks/blocked.log\n")
        sys.stderr.write("Action: Command execution was aborted to prevent irreversible loss.\n")
        sys.stderr.write("="*70 + "\n\n")
        sys.exit(1)

    # Allowed command
    sys.exit(0)

if __name__ == "__main__":
    main()
