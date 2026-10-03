#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook to block destructive bash commands.
Complies with Anthropic Claude Code hooks specification.
"""
import sys
import os
import json
import re
from datetime import datetime

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")
os.makedirs(os.path.dirname(BLOCKED_LOG_PATH), exist_ok=True)

FORBIDDEN_PATTERNS = [
    (r"\brm\s+-(?:rf|fr|r\s+f|f\s+r)\b", "Recursive force removal (rm -rf)"),
    (r"\bDROP\s+TABLE\b", "SQL DROP TABLE operation"),
    (r"\bgit\s+push\s+(?:.*--force|-f\b)", "Forced git push (git push --force)"),
    (r"\bTRUNCATE(?:\s+TABLE)?\b", "SQL TRUNCATE operation"),
    (r"\bDELETE\s+FROM\s+\w+(?!\s+WHERE\b)", "Unrestricted SQL DELETE FROM without WHERE clause"),
]

def check_command(command_str, cwd=""):
    for pattern, reason in FORBIDDEN_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] [BLOCKED: {reason}] [CWD: {cwd}] Command: {command_str}\n"
            with open(BLOCKED_LOG_PATH, "a") as f:
                f.write(log_entry)
            return False, reason
    return True, None

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    cwd = payload.get("cwd", os.getcwd())

    if tool_name in ["Bash", "terminal", "execute_command"]:
        cmd = tool_input.get("command", "")
        allowed, reason = check_command(cmd, cwd)
        if not allowed:
            print(json.dumps({
                "decision": "block",
                "reason": f"SAFETY BLOCKED: {reason}. This destructive command is prevented by safety policy."
            }))
            sys.exit(1)

    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

if __name__ == "__main__":
    main()
