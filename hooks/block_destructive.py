#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code to block destructive bash commands.
Complies with Claude Code hook specifications.
"""

import sys
import re
import os
import json
from datetime import datetime

def check_command(command: str, cwd: str = ".") -> tuple[bool, str]:
    cleaned = command.strip()

    # 1. Recursive removal
    if re.search(r"\brm\s+.*(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive|-r\b)", cleaned, re.IGNORECASE):
        return True, "Recursive deletion ('rm -rf' / 'rm -r')"

    # 2. DROP TABLE / DROP DATABASE
    if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", cleaned, re.IGNORECASE):
        return True, "Destructive SQL ('DROP TABLE/DATABASE')"

    # 3. Git force push
    if re.search(r"\bgit\s+push\s+.*(--force\b|-f\b|\+)", cleaned, re.IGNORECASE):
        return True, "Force-pushing git branches ('git push --force')"

    # 4. TRUNCATE TABLE
    if re.search(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_`\"']+", cleaned, re.IGNORECASE):
        return True, "SQL table truncation ('TRUNCATE')"

    # 5. DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", cleaned, re.IGNORECASE) and not re.search(r"\bWHERE\b", cleaned, re.IGNORECASE):
        return True, "Unbounded SQL deletion ('DELETE FROM' without WHERE clause)"

    return False, ""

def log_blocked_attempt(command: str, reason: str, cwd: str):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "command": command,
        "reason": reason,
        "project_path": cwd
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main():
    input_data = sys.stdin.read()
    command = ""
    cwd = os.getcwd()

    if input_data:
        try:
            payload = json.loads(input_data)
            tool_input = payload.get("input", {})
            if isinstance(tool_input, dict):
                command = tool_input.get("command", "") or tool_input.get("CommandLine", "")
                cwd = tool_input.get("cwd", cwd)
            elif isinstance(tool_input, str):
                command = tool_input
        except Exception:
            command = input_data.strip()

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command, cwd)
    if is_blocked:
        log_blocked_attempt(command, reason, cwd)
        sys.stderr.write(f"\n❌ [BLOCKED BY HOOK] Intercepted destructive command: {reason}\n")
        sys.stderr.write(f"Command: {command}\n")
        sys.stderr.write(f"Logged to: ~/.claude/hooks/blocked.log\n\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
