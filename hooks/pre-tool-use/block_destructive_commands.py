#!/usr/bin/env python3
"""
Pre-Tool-Use Hook: Block Destructive Bash Commands
Part of Claude Code Security Suite (Bounty #3)

Intercepts dangerous bash commands before execution in Claude Code.
Blocks:
  - rm -rf / rm -fr / rm -r -f / rm --recursive --force
  - DROP TABLE
  - git push --force / git push -f / force push refspecs (+ref)
  - TRUNCATE / TRUNCATE TABLE
  - DELETE FROM without a WHERE clause

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import sys
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

# Destructive command patterns
PATTERNS = [
    {
        "id": "RM_RF",
        "description": "Recursive forced deletion (rm -rf)",
        "regex": re.compile(r"\brm\s+[^\n;]*?(?:-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive|-r\s+-f|-f\s+-r)\b", re.IGNORECASE)
    },
    {
        "id": "DROP_TABLE",
        "description": "SQL DROP TABLE operation",
        "regex": re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
    },
    {
        "id": "GIT_PUSH_FORCE",
        "description": "Forced git push (git push --force or git push -f)",
        "regex": re.compile(r"\bgit\s+push\b[^\n;]*(\s+-f\b|\s+--force\b|\s+--force-with-lease\b|\s+\+[a-zA-Z0-9_\-\/]+)", re.IGNORECASE)
    },
    {
        "id": "TRUNCATE",
        "description": "SQL TRUNCATE operation",
        "regex": re.compile(r"\bTRUNCATE(\s+TABLE)?\s+[a-zA-Z0-9_.\"']+", re.IGNORECASE)
    },
    {
        "id": "UNGUARDED_DELETE",
        "description": "SQL DELETE FROM without a WHERE clause",
        "regex": re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.\"']+\s*(?:;\s*$|$|\)(?!\s*WHERE\b))", re.IGNORECASE)
    }
]


def check_command(command: str) -> tuple[bool, str, str]:
    """
    Checks if a command matches any destructive pattern.
    Returns: (is_blocked, pattern_id, description)
    """
    if not command or not isinstance(command, str):
        return False, "", ""

    # Special check for DELETE FROM without WHERE across multiple statements
    statements = re.split(r"[;&|\n]", command)
    for stmt in statements:
        cleaned = stmt.strip()
        if not cleaned:
            continue
        # Check DELETE FROM specifically
        if re.search(r"\bDELETE\s+FROM\b", cleaned, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", cleaned, re.IGNORECASE):
                return True, "UNGUARDED_DELETE", "SQL DELETE FROM without a WHERE clause"

    for p in PATTERNS:
        if p["id"] == "UNGUARDED_DELETE":
            continue
        if p["regex"].search(command):
            return True, p["id"], p["description"]

    return False, "", ""


def log_blocked(command: str, rule: str, cwd: str) -> None:
    """Logs blocked command to ~/.claude/hooks/blocked.log with timestamp and project path."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = (
            f"[{timestamp}] BLOCKED_RULE={rule} "
            f"PROJECT_PATH={cwd} "
            f"COMMAND={command!r}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[pre-tool-use-hook] Warning: could not write to {LOG_FILE}: {e}\n")


def extract_command_from_payload() -> tuple[str, str]:
    """
    Extracts the command and working directory from stdin payload or sys.argv.
    Claude Code passes tool use input as JSON via stdin.
    """
    cwd = os.getcwd()

    # Case 1: JSON payload via stdin
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                data = json.loads(stdin_content)
                # Claude Code PreToolUse structure
                tool_input = data.get("tool_input", {})
                if isinstance(tool_input, dict):
                    cmd = tool_input.get("command") or tool_input.get("cmd")
                    if cmd:
                        return str(cmd), data.get("project_path") or cwd
                # Raw command string or direct tool payload
                if "command" in data:
                    return str(data["command"]), cwd
        except Exception:
            pass

    # Case 2: Command passed as CLI argument
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]), cwd

    return "", cwd


def main():
    command, cwd = extract_command_from_payload()
    if not command:
        # No command to check
        sys.exit(0)

    is_blocked, rule_id, description = check_command(command)
    if is_blocked:
        log_blocked(command, rule_id, cwd)

        # Output detailed explanatory error to Claude Code
        error_msg = (
            f"\n⛔ [SECURITY INTERCEPT] Destructive bash command blocked by PreToolUse hook!\n"
            f"  - Violated Rule : {rule_id} ({description})\n"
            f"  - Attempted Cmd : {command}\n"
            f"  - Project Path  : {cwd}\n"
            f"  - Logged To     : {LOG_FILE}\n\n"
            f"Reason: This command contains irreversible operations that can destroy files, databases, or git history.\n"
            f"Please verify your intent, use safe dry-runs, or supply explicit filters (e.g. WHERE clause for SQL deletes).\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)

    # Command is safe
    sys.exit(0)


if __name__ == "__main__":
    main()
