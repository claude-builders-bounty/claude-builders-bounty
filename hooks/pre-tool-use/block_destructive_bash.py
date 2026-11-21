#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Destructive Bash & SQL Command Blocker (Bounty Issue #3)
Follows the official Claude Code hooks format (~/.claude/hooks/block_destructive_bash.py).

Blocks:
  1. rm -rf (or rm -fr / rm --recursive --force)
  2. DROP TABLE
  3. git push --force (or git push -f)
  4. TRUNCATE (SQL TRUNCATE TABLE)
  5. DELETE FROM without a WHERE clause

Logs every blocked attempt to ~/.claude/hooks/blocked.log with:
  timestamp | project_path | reason | attempted_command
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


def detect_destructive_reason(command: str) -> str | None:
    if not command or not command.strip():
        return None

    if re.search(
        r"(?:^|[;&|()\s])(?:sudo\s+)?rm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*[rf][a-zA-Z]*|(?=[^\n;]*\s-[a-zA-Z]*r)(?=[^\n;]*\s-[a-zA-Z]*f)|(?=[^\n;]*--recursive)(?=[^\n;]*--force))",
        command,
        re.IGNORECASE,
    ):
        return "Blocked destructive command: 'rm -rf' recursive force deletion is prohibited."

    if re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE):
        return "Blocked destructive SQL statement: 'DROP TABLE' is prohibited."

    if re.search(
        r"\bgit\s+push\b[^\n;&|]*(?:\s--force(?![-a-zA-Z])|\s-[a-zA-Z]*f\b)",
        command,
        re.IGNORECASE,
    ):
        return "Blocked destructive Git command: 'git push --force' (-f) is prohibited."

    if re.search(r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_`\"'.]+", command, re.IGNORECASE):
        return "Blocked destructive SQL statement: 'TRUNCATE' is prohibited."

    for match in re.finditer(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"'.]+([^;\"']*)", command, re.IGNORECASE):
        tail = match.group(1) or ""
        if not re.search(r"\bWHERE\b", tail, re.IGNORECASE):
            return "Blocked destructive SQL statement: 'DELETE FROM' without a WHERE clause is prohibited."

    return None


def log_blocked_attempt(project_path: str, command: str, reason: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        one_line_cmd = command.replace("\n", "\\n")
        entry = f"{ts} | project={project_path} | reason={reason} | command={one_line_cmd}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def main() -> int:
    raw_stdin = sys.stdin.read().strip()
    command = ""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    tool_name = "Bash"

    if raw_stdin:
        try:
            payload = json.loads(raw_stdin)
            tool_name = payload.get("tool_name") or payload.get("tool") or "Bash"
            tool_input = payload.get("tool_input") or payload.get("input") or {}
            if isinstance(tool_input, dict):
                command = str(tool_input.get("command") or tool_input.get("cmd") or "")
            elif isinstance(tool_input, str):
                command = tool_input
            project_path = (
                payload.get("cwd")
                or payload.get("project_dir")
                or payload.get("projectPath")
                or project_path
            )
        except json.JSONDecodeError:
            command = raw_stdin

    if tool_name.lower() not in ("bash", "shell", "terminal", ""):
        return 0

    reason = detect_destructive_reason(command)
    if not reason:
        return 0

    log_blocked_attempt(project_path, command, reason)

    message = (
        f"[Claude Code PreToolUse Guard] {reason}\n"
        f"Attempted command: {command}\n"
        f"Project path: {project_path}\n"
        f"Logged to: {LOG_FILE}"
    )

    response = {
        "decision": "block",
        "reason": message,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
    }
    print(json.dumps(response))
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
