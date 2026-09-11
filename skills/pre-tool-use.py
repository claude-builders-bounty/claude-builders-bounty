#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Interceptor
Intercepts and blocks high-risk destructive shell commands before execution.
Compliant with Claude Code hook specifications.
"""

import sys
import os
import re
import json
from datetime import datetime, timezone

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

def is_rm_rf(cmd):
    # Matches rm with both recursive (-r, -R) and force (-f) flags, whether combined or separate
    if not re.search(r"\brm\b", cmd, re.IGNORECASE):
        return False
    # Check if flags include r/R and f
    has_r = bool(re.search(r"\s-[a-zA-Z]*[rR]", cmd))
    has_f = bool(re.search(r"\s-[a-zA-Z]*f", cmd))
    return has_r and has_f

def is_unbounded_delete(cmd):
    match = re.search(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_.\"']+)(.*)", cmd, re.IGNORECASE)
    if match:
        rest = match.group(2)
        end_match = re.search(r"[;'\"|]", rest)
        sql_clause = rest[:end_match.start()] if end_match else rest
        return not bool(re.search(r"\bWHERE\b", sql_clause, re.IGNORECASE))
    return False

DESTRUCTIVE_RULES = [
    {
        "id": "RM_RF",
        "name": "Recursive Force Removal",
        "check": is_rm_rf,
        "reason": "Indiscriminate recursive file deletion (rm -rf) can destroy critical project or system files."
    },
    {
        "id": "SQL_DROP_TABLE",
        "name": "SQL Drop Table",
        "check": lambda cmd: bool(re.search(r"\bDROP\s+TABLE\b", cmd, re.IGNORECASE)),
        "reason": "DROP TABLE irreversibly deletes database tables and schemas."
    },
    {
        "id": "SQL_TRUNCATE",
        "name": "SQL Truncate Table",
        "check": lambda cmd: bool(re.search(r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_.]+", cmd, re.IGNORECASE)),
        "reason": "TRUNCATE irreversibly purges all data from the target table."
    },
    {
        "id": "SQL_UNBOUNDED_DELETE",
        "name": "Unbounded SQL Delete",
        "check": is_unbounded_delete,
        "reason": "DELETE FROM without a WHERE clause will wipe every record in the table."
    },
    {
        "id": "GIT_PUSH_FORCE",
        "name": "Git Force Push",
        "check": lambda cmd: bool(re.search(r"\bgit\s+push\s+.*(?:--force|-f\b|--force-with-lease)", cmd, re.IGNORECASE)),
        "reason": "Force pushing can overwrite remote team commit history."
    }
]

def log_blocked_attempt(command, project_path, rule_matched):
    os.makedirs(os.path.dirname(BLOCKED_LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = (
        f"[{timestamp}] BLOCKED_RULE={rule_matched['id']} | "
        f"PROJECT={project_path} | "
        f"CMD=\"{command.strip()}\"\n"
    )
    try:
        with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to log: {e}\n")

def evaluate_command(command, project_path):
    if not command or not command.strip():
        return True, None

    for rule in DESTRUCTIVE_RULES:
        if rule["check"](command):
            log_blocked_attempt(command, project_path, rule)
            return False, rule

    return True, None

def get_stdin_content_safe():
    if sys.stdin.isatty():
        return None
    try:
        if sys.platform == "win32":
            import msvcrt
            import ctypes
            from ctypes import wintypes
            h = msvcrt.get_osfhandle(sys.stdin.fileno())
            avail = wintypes.DWORD()
            res = ctypes.windll.kernel32.PeekNamedPipe(h, None, 0, None, ctypes.byref(avail), None)
            if not res or avail.value == 0:
                return None
        else:
            import select
            r, _, _ = select.select([sys.stdin], [], [], 0)
            if not r:
                return None
        return sys.stdin.read()
    except Exception:
        return None

def main():
    command = ""
    project_path = os.getcwd()

    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        stdin_content = get_stdin_content_safe()
        if stdin_content:
            try:
                data = json.loads(stdin_content)
                command = data.get("command") or data.get("tool_input", {}).get("command") or ""
                project_path = data.get("project_path") or data.get("cwd") or os.getcwd()
            except Exception:
                command = stdin_content.strip()

    if not command:
        print("=" * 64)
        print("🛡️  Claude Code Safety Hook: Destructive Command Interceptor")
        print("=" * 64)
        print("Status: Active & Listening for Claude Code tool invocations")
        print("\nEnforced Safety Rules:")
        for r in DESTRUCTIVE_RULES:
            print(f"  • [{r['id']}] {r['name']}")
        print("=" * 64)
        sys.exit(0)

    allowed, violated_rule = evaluate_command(command, project_path)

    if not allowed:
        sys.stderr.write("\n" + "=" * 64 + "\n")
        sys.stderr.write(f"🛑 [SAFETY HOOK BLOCKED] Destructive Command Intercepted\n")
        sys.stderr.write("=" * 64 + "\n")
        sys.stderr.write(f"Violated Rule : {violated_rule['name']} ({violated_rule['id']})\n")
        sys.stderr.write(f"Attempted Cmd : {command.strip()}\n")
        sys.stderr.write(f"Why Blocked   : {violated_rule['reason']}\n")
        sys.stderr.write(f"Logged To     : {BLOCKED_LOG_PATH}\n")
        sys.stderr.write("=" * 64 + "\n\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
