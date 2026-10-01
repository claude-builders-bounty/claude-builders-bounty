#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Interceptor Hook
Catches and blocks high-risk destructive commands before execution.
Complies with Claude Code hook specifications (~/.claude/hooks/).
"""

import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_LOG_PATH = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))

DANGEROUS_PATTERNS = [
    {
        "id": "RM_RF",
        "pattern": re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive)\b"),
        "reason": "Recursive forced deletion (rm -rf) detected. High risk of irreversible data destruction."
    },
    {
        "id": "GIT_FORCE_PUSH",
        "pattern": re.compile(r"git\s+push.*(\s--force\b|\s-f\b|\s--force-with-lease\b)"),
        "reason": "Force pushing to remote repository can overwrite commit history and destroy branch state."
    },
    {
        "id": "SQL_DROP_TABLE",
        "pattern": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "reason": "Direct database schema destruction (DROP TABLE) is prohibited in automated execution."
    },
    {
        "id": "SQL_TRUNCATE",
        "pattern": re.compile(r"\bTRUNCATE(\s+TABLE)?\b", re.IGNORECASE),
        "reason": "Complete table wipe (TRUNCATE) detected. Destroys all persistent database records."
    },
    {
        "id": "SQL_UNGUARDED_DELETE",
        "pattern": re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_\.\"`\]\[]+(?!\s+WHERE\b)[;\s]*$", re.IGNORECASE),
        "reason": "Unrestricted table wipe (DELETE FROM without a WHERE clause) detected."
    }
]

def log_blocked_command(command: str, project_path: str, reason: str):
    try:
        BLOCKED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [BLOCKED] project={project_path} | reason={reason} | command={command}\n"
        with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[Hook Warning] Failed to write to blocked.log: {e}\n")

def check_command(command_str: str, project_path: str) -> bool:
    if not command_str:
        return True

    for item in DANGEROUS_PATTERNS:
        if item["pattern"].search(command_str):
            reason = item["reason"]
            log_blocked_command(command_str, project_path, reason)
            error_msg = (
                f"\n⛔ [CLAUDE SECURITY HOOK BLOCKED] Execution Denied!\n"
                f"------------------------------------------------------------------\n"
                f"Command : {command_str}\n"
                f"Reason  : {reason}\n"
                f"Audit   : Logged to {BLOCKED_LOG_PATH}\n"
                f"Action  : Please refine your command with safe, non-destructive flags.\n"
                f"------------------------------------------------------------------\n"
            )
            sys.stderr.write(error_msg)
            return False
    return True

def main():
    project_path = os.getcwd()

    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
            if raw_input.strip():
                try:
                    payload = json.loads(raw_input)
                    tool_name = payload.get("tool_name", "")
                    tool_input = payload.get("tool_input", {})
                    
                    cmd = ""
                    if isinstance(tool_input, dict):
                        cmd = tool_input.get("command", "") or tool_input.get("cmd", "")
                    elif isinstance(tool_input, str):
                        cmd = tool_input

                    if tool_name in ("bash", "execute_command", "run_command", "terminal") or cmd:
                        if not check_command(cmd, project_path):
                            sys.exit(1)
                except json.JSONDecodeError:
                    if not check_command(raw_input.strip(), project_path):
                        sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"[Hook Error] {e}\n")

    if len(sys.argv) > 1:
        cmd_arg = " ".join(sys.argv[1:])
        if not check_command(cmd_arg, project_path):
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
