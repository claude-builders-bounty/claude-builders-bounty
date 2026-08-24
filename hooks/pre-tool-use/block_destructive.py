#!/usr/bin/env python3
"""
Pre-tool-use security hook for Claude Code.
Blocks destructive bash and SQL commands before execution and logs incidents.
"""
import sys
import json
import re
import os
import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*\s+.*", "Destructive recursive force-removal (rm -rf)"),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "Dangerous database object drop (DROP TABLE/DATABASE)", re.IGNORECASE),
    (r"\bgit\s+push\b.*(\s+--force\b|\s+-f\b)", "Unsafe git force-push (git push --force)"),
    (r"\bTRUNCATE(\s+TABLE)?\b", "Database table truncate operation (TRUNCATE)", re.IGNORECASE),
    (r"\bDELETE\s+FROM\s+\w+\s*(?:;|\s*$)", "Unconditional table deletion without WHERE clause", re.IGNORECASE),
    (r"\b(mkfs(\.\w+)?|dd\s+if=.*of=/dev/)", "Raw disk formatting / overwriting operation"),
    (r">\s*/dev/sd[a-z]", "Direct block device write redirect"),
]

def get_log_path():
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "blocked.log"

def log_blocked(command: str, reason: str, cwd: str):
    log_file = get_log_path()
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": command,
        "reason": reason,
        "cwd": cwd,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def check_command(command: str) -> tuple[bool, str]:
    for item in BLOCKED_PATTERNS:
        pattern = item[0]
        reason = item[1]
        flags = item[2] if len(item) > 2 else 0
        if re.search(pattern, command, flags):
            return False, reason
    return True, ""

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        data = json.loads(raw_input)
    except Exception:
        # Fallback if command string passed as argument
        if len(sys.argv) > 1:
            data = {"tool_name": "Bash", "tool_input": {"command": " ".join(sys.argv[1:])}}
        else:
            sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if tool_name.lower() in ("bash", "execute_command", "run_command") and command:
        allowed, reason = check_command(command)
        if not allowed:
            cwd = os.getcwd()
            log_blocked(command, reason, cwd)
            sys.stderr.write(
                f"\n[SECURITY HOOK BLOCKED] Execution stopped.\n"
                f"Reason: {reason}\n"
                f"Command: {command}\n"
                f"Logged to: ~/.claude/hooks/blocked.log\n"
            )
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
