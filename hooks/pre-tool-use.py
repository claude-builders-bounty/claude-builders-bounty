#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code to block destructive bash commands.
Complies with Claude Code hooks format. Logs blocks to ~/.claude/hooks/blocked.log
"""

import sys
import json
import re
import os
import shlex
from datetime import datetime
from pathlib import Path

# Patterns evaluated against unquoted shell tokens
DESTRUCTIVE_RULES = [
    # (Regex pattern, Description)
    (r"^\s*rm\s+.*-[rRfF]*[rR][rRfF]*\b", "Recursive file deletion (rm -rf)"),
    (r"\bDROP\s+TABLE\b", "SQL DROP TABLE statement"),
    (r"\bgit\s+push\s+.*(--force|-f)\b", "Forced git push (--force)"),
    (r"\bTRUNCATE(\s+TABLE)?\b", "SQL TRUNCATE statement"),
]

def get_log_file():
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "blocked.log"

def log_blocked(command: str, reason: str, cwd: str):
    log_file = get_log_file()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "command": command,
        "cwd": cwd or os.getcwd()
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def strip_quoted_strings(command: str) -> str:
    """Removes single/double quoted literals from command to avoid false positives in commit messages / echoes."""
    # Matches anything inside single or double quotes
    return re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"", "''", command)

def check_command(command: str) -> tuple[bool, str]:
    if not command:
        return False, ""
    
    # Strip literal arguments (like git commit -m "rm -rf something")
    sanitized = strip_quoted_strings(command)
    
    # Check destructive rules
    for pattern, reason in DESTRUCTIVE_RULES:
        if re.search(pattern, sanitized, re.IGNORECASE):
            return True, reason
            
    # Check DELETE FROM without WHERE (on sanitized command)
    if re.search(r"\bDELETE\s+FROM\b", sanitized, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", sanitized, re.IGNORECASE):
            return True, "SQL DELETE FROM statement without a WHERE clause"
            
    return False, ""

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        data = json.loads(raw_input)
    except Exception:
        raw_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
        data = {"tool": "Bash", "parameters": {"command": raw_input}, "cwd": os.getcwd()}

    tool_name = data.get("tool") or data.get("tool_name", "")
    params = data.get("parameters") or data.get("input") or {}
    cwd = data.get("cwd") or os.getcwd()
    
    if str(tool_name).lower() in ["bash", "terminal", "execute_command", "shell", ""]:
        command = params.get("command") or params.get("cmd") or ""
        if not command and isinstance(params, str):
            command = params
        
        is_blocked, reason = check_command(command)
        if is_blocked:
            log_blocked(command, reason, cwd)
            error_message = (
                f"\n[SECURITY INTERCEPT] Command blocked by pre-tool-use hook!\n"
                f"Reason: {reason}\n"
                f"Attempted: {command}\n"
                f"Log saved to: ~/.claude/hooks/blocked.log\n"
            )
            sys.stderr.write(error_message)
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
