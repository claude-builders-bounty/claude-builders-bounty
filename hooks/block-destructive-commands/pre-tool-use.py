#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
=============================================================
Safeguards developer environments against catastrophic bash tool executions:
- Intercepts dangerous destructive commands before execution.
- Blocks rm -rf, DROP TABLE, git push --force, TRUNCATE, and unconstrained DELETE FROM.
- Logs blocked attempts to ~/.claude/hooks/blocked.log with full audit metadata.
- Outputs human-readable rejection explanations for Claude to auto-correct safely.
"""

import os
import sys
import json
import re
import datetime
from pathlib import Path

DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_RULES = [
    {
        "name": "Recursive Force File Deletion (rm -rf)",
        "pattern": re.compile(
            r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+|--(?:recursive|force)\s+)+",
            re.IGNORECASE
        ),
        "explanation": "Dangerous recursive deletion ('rm -rf') is prohibited to prevent catastrophic data loss."
    },
    {
        "name": "SQL Drop Table",
        "pattern": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "explanation": "Destructive SQL command 'DROP TABLE' detected. Direct schema destruction is blocked."
    },
    {
        "name": "Git Force Push",
        "pattern": re.compile(r"\bgit\s+push\b.*?(?:--force|-f\b|--force-with-lease\b)", re.IGNORECASE),
        "explanation": "Destructive git push force detected. Rewriting remote commit history is blocked."
    },
    {
        "name": "SQL Truncate Table",
        "pattern": re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_`\"\[\]]+", re.IGNORECASE),
        "explanation": "Destructive SQL command 'TRUNCATE' detected. Wiping entire table contents is blocked."
    },
    {
        "name": "Unconstrained SQL Delete (Missing WHERE clause)",
        "pattern": re.compile(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_`\"\[\]]+)(?![\s\S]*\bWHERE\b)", re.IGNORECASE),
        "explanation": "SQL 'DELETE FROM' without a WHERE clause will wipe the entire table. Always provide an explicit WHERE filter."
    }
]

def log_blocked(command: str, project_path: str, rule_name: str, log_file: Path = DEFAULT_LOG_PATH):
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{now_str}] [PROJECT: {project_path}] "
            f"BLOCKED: {rule_name} | COMMAND: {command.strip()}\n"
        )
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to write to blocked log: {e}\n")

def check_command(command: str, project_path: str = None, log_file: Path = DEFAULT_LOG_PATH):
    if not command or not isinstance(command, str):
        return True, ""
    
    if project_path is None:
        project_path = os.getcwd()
        
    for rule in DANGEROUS_RULES:
        if rule["pattern"].search(command):
            # Special check for DELETE FROM: ensure WHERE isn't in subsequent statements or multi-queries
            if rule["name"] == "Unconstrained SQL Delete (Missing WHERE clause)":
                # If WHERE exists anywhere after DELETE FROM in the same statement, allow
                statements = command.split(";")
                is_violation = False
                for stmt in statements:
                    if re.search(r"\bDELETE\s+FROM\b", stmt, re.IGNORECASE) and not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
                        is_violation = True
                        break
                if not is_violation:
                    continue
            
            log_blocked(command, project_path, rule["name"], log_file)
            rejection_msg = (
                f"\n🚨 [PRE-TOOL-USE HOOK BLOCKED] Execution Aborted!\n"
                f"Rule: {rule['name']}\n"
                f"Reason: {rule['explanation']}\n"
                f"Offending Command: {command.strip()}\n"
                f"Audit Trail: Logged to {log_file}\n"
            )
            return False, rejection_msg
            
    return True, ""

def main():
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    raw_input = ""
    
    # 1. Read from stdin (Claude Code JSON hook payload or raw piped string)
    if not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()
        
    # 2. Support CLI argument fallback
    if not raw_input and len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])

    if not raw_input:
        sys.exit(0)

    command_to_check = raw_input
    # Parse JSON if Claude Code sends structured payload: {"tool": "Bash", "tool_input": {"command": "..."}}
    try:
        parsed = json.loads(raw_input)
        if isinstance(parsed, dict):
            if "tool_input" in parsed and isinstance(parsed["tool_input"], dict):
                command_to_check = parsed["tool_input"].get("command", "")
            elif "command" in parsed:
                command_to_check = parsed.get("command", "")
    except Exception:
        pass

    allowed, message = check_command(command_to_check, project_path)
    if not allowed:
        sys.stderr.write(message)
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
