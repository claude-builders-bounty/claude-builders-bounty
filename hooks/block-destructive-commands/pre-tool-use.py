#!/usr/bin/env python3
"""
🛡️ Claude Code Pre-Tool-Use Hook: Destructive Command Shield
Intercepts and blocks dangerous/destructive bash commands before execution.
Logs all blocked events to ~/.claude/hooks/blocked.log.
"""

import sys
import os
import json
import re
from datetime import datetime

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Forbidden pattern definitions with detailed explanations
BLOCKED_PATTERNS = [
    {
        "id": "rm_rf",
        "name": "Recursive Force Removal (rm -rf)",
        "regex": re.compile(
            r"(?:^|[\s;&|])rm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*[rf][a-zA-Z]*|--recursive\s+--force|--force\s+--recursive)",
            re.IGNORECASE
        ),
        "reason": "Destructive recursive deletion of files/directories. Use specific, non-forced targets or trash utilities."
    },
    {
        "id": "drop_table",
        "name": "Database Table/Schema Destruction (DROP TABLE/DATABASE)",
        "regex": re.compile(
            r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA|VIEW)\b",
            re.IGNORECASE
        ),
        "reason": "Irreversible destruction of database tables or schemas. Use migrations or explicit down-scripts."
    },
    {
        "id": "git_force_push",
        "name": "Git Force Push (git push --force)",
        "regex": re.compile(
            r"\bgit\s+push\s+.*?(?:--force|-f|--force-with-lease)\b",
            re.IGNORECASE
        ),
        "reason": "Overwrites remote git history and risks losing team commits. Use regular push or fast-forward merges."
    },
    {
        "id": "truncate_table",
        "name": "SQL Truncation (TRUNCATE)",
        "regex": re.compile(
            r"\bTRUNCATE(?:\s+TABLE)?\b",
            re.IGNORECASE
        ),
        "reason": "Mass truncation deletes all rows from database tables immediately without rollback log."
    },
    {
        "id": "delete_without_where",
        "name": "SQL Delete Without WHERE Clause",
        "regex": re.compile(
            r"\bDELETE\s+FROM\s+([`\"'\w\.]+)(?:\s*;|\s*$|\s+(?!WHERE\b))",
            re.IGNORECASE
        ),
        "reason": "Unfiltered DELETE FROM deletes all records in the table. Must include an explicit WHERE condition."
    }
]


def extract_command_and_context():
    """Extract command string and project cwd from stdin (JSON or text) or CLI args."""
    command = ""
    cwd = os.getcwd()

    # 1. Check CLI arguments
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    # 2. Check STDIN if provided
    if not command and not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    if isinstance(payload, dict):
                        # Claude Code hook payload format
                        if "tool_input" in payload and isinstance(payload["tool_input"], dict):
                            command = payload["tool_input"].get("command", "") or payload["tool_input"].get("cmd", "")
                        elif "command" in payload:
                            command = payload["command"]
                        cwd = payload.get("cwd", cwd)
                    else:
                        command = raw_input
                except json.JSONDecodeError:
                    command = raw_input
        except Exception:
            pass

    return command.strip(), cwd


def check_command(command: str):
    """Checks if the command matches any blocked destructive patterns."""
    if not command:
        return None

    # Check against each forbidden pattern
    for rule in BLOCKED_PATTERNS:
        match = rule["regex"].search(command)
        if match:
            # Special refinement for DELETE FROM: ensure there is really no WHERE clause
            if rule["id"] == "delete_without_where":
                # If there's a WHERE clause anywhere after DELETE FROM, allow it
                if re.search(r"\bDELETE\s+FROM\b.*?\bWHERE\b", command, re.IGNORECASE | re.DOTALL):
                    continue
            return rule

    return None


def log_blocked_attempt(rule: dict, command: str, cwd: str):
    """Appends blocked attempt details to ~/.claude/hooks/blocked.log."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] BLOCKED | Rule: {rule['name']} | "
            f"Path: {cwd} | Command: {command}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def main():
    command, cwd = extract_command_and_context()

    if not command:
        # No command to evaluate, proceed safely
        sys.exit(0)

    matched_rule = check_command(command)

    if matched_rule:
        # Log the incident
        log_blocked_attempt(matched_rule, command, cwd)

        # Output detailed explanation to Claude and user
        error_msg = f"""
🛑 [CLAUDE HOOK] Destructive Command Blocked!
────────────────────────────────────────────────────────────────
Pattern Detected : {matched_rule['name']}
Attempted Command: {command}
Project Location : {cwd}
Reason           : {matched_rule['reason']}
Audit Log Entry  : Saved to {LOG_FILE}
────────────────────────────────────────────────────────────────
Action Aborted: To protect your data, source control, and database integrity,
this command was prevented from executing. If this action is strictly required,
please execute it manually in your shell with explicit human confirmation.
"""
        sys.stderr.write(error_msg.strip() + "\n")
        # Exit with code 2 to strictly block tool execution in Claude Code PreToolUse contract
        sys.exit(2)

    # Safe command: exit 0 to allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
