#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Guard
Blocks dangerous bash operations before execution and logs incidents.
"""

import sys
import json
import re
import os
import select
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

BLOCKED_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RULES = [
    {
        "id": "rm_rf",
        "description": "Recursive forced file deletion (rm -rf / rm -fr)",
        "pattern": re.compile(r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)+|rm\s+--recursive\s+--force|rm\s+--force\s+--recursive", re.IGNORECASE),
        "explanation": "Mass deletion using 'rm -rf' risks unrecoverable data loss."
    },
    {
        "id": "drop_table",
        "description": "SQL DROP TABLE statement",
        "pattern": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "explanation": "Executing 'DROP TABLE' destroys database schemas and persistent records."
    },
    {
        "id": "git_push_force",
        "description": "Git force push",
        "pattern": re.compile(r"\bgit\s+push\b.*?(?:--force|-f\b|--force-with-lease)", re.IGNORECASE),
        "explanation": "Force-pushing overwrites remote history and can destroy collaborators' commits."
    },
    {
        "id": "truncate_table",
        "description": "SQL TRUNCATE statement",
        "pattern": re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[\w`\"']+", re.IGNORECASE),
        "explanation": "Executing 'TRUNCATE' unconditionally empties table records."
    },
    {
        "id": "delete_without_where",
        "description": "SQL DELETE FROM without WHERE clause",
        "pattern": re.compile(r"\bDELETE\s+FROM\s+[`\"']?[\w]+[`\"']?(?:\s*;|\s*$|(?!\s+WHERE\b)[^;]*;)", re.IGNORECASE),
        "explanation": "'DELETE FROM' without a 'WHERE' clause wipes every row in the target table."
    }
]

def check_command(command: str) -> Tuple[bool, Optional[str], Optional[str]]:
    cmd = command.strip()
    if not cmd:
        return False, None, None

    delete_match = re.search(r"\bDELETE\s+FROM\s+[`\"']?[\w]+[`\"']?", cmd, re.IGNORECASE)
    if delete_match:
        sql_remainder = cmd[delete_match.end():]
        statement = sql_remainder.split(";")[0]
        if not re.search(r"\bWHERE\b", statement, re.IGNORECASE):
            return True, "delete_without_where", "'DELETE FROM' without a 'WHERE' clause wipes every row in the target table."

    for rule in RULES:
        if rule["id"] == "delete_without_where":
            continue
        if rule["pattern"].search(cmd):
            return True, rule["id"], rule["explanation"]

    return False, None, None

def log_blocked(command: str, project_dir: str, rule_id: str, log_path: Path = BLOCKED_LOG_PATH) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] BLOCKED: \"{command}\" | PROJECT: \"{project_dir}\" | RULE: {rule_id}\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked log ({e})\n")

def parse_input() -> Tuple[str, str]:
    # 1. If explicit CLI arguments provided, prioritize them
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if "--command" in args:
            idx = args.index("--command")
            cmd = args[idx + 1] if idx + 1 < len(args) else ""
            proj = os.getcwd()
            if "--project-dir" in args:
                pidx = args.index("--project-dir")
                proj = args[pidx + 1] if pidx + 1 < len(args) else proj
            return cmd, proj
        return args[0], os.getcwd()

    # 2. Non-blocking check for stdin data (Claude Code JSON payload)
    try:
        rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
        if rlist:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                data = json.loads(stdin_content)
                tool = data.get("tool") or data.get("tool_name") or ""
                tool_input = data.get("tool_input") or data.get("input") or {}

                if tool and tool.lower() not in ("bash", "sh", "terminal", "exec"):
                    return "", os.getcwd()

                command = ""
                if isinstance(tool_input, dict):
                    command = tool_input.get("command") or tool_input.get("cmd") or ""
                elif isinstance(tool_input, str):
                    command = tool_input

                if not command and "command" in data:
                    command = data["command"]

                project_dir = data.get("cwd") or data.get("project_dir") or data.get("projectPath") or os.getcwd()
                return str(command), str(project_dir)
    except Exception:
        pass

    return "", os.getcwd()

def main():
    command, project_dir = parse_input()

    if not command:
        sys.exit(0)

    is_blocked, rule_id, explanation = check_command(command)

    if is_blocked:
        log_blocked(command, project_dir, rule_id)
        msg = (
            f"\n⛔ [SAFETY GUARD INTERCEPTED DANGEROUS COMMAND]\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Command:     {command}\n"
            f"Policy Rule: {rule_id}\n"
            f"Reason:      {explanation}\n"
            f"Action:      Blocked by Claude Code pre-tool-use security hook.\n"
            f"Log Entry:   Appended to ~/.claude/hooks/blocked.log\n"
            f"Advice:      Use non-destructive alternatives or request manual user execution.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        sys.stderr.write(msg)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
