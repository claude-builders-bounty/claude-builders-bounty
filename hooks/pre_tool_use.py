#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code.
Intercepts dangerous bash commands before execution and blocks:
- rm -rf
- DROP TABLE
- git push --force
- TRUNCATE
- DELETE FROM without a WHERE clause

Logs blocked attempts to ~/.claude/hooks/blocked.log with ISO timestamp,
attempted command, and project path.
"""

import sys
import os
import re
import json
from datetime import datetime, timezone

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")


def check_rm_rf(cmd: str) -> str | None:
    """Checks for recursive force remove patterns (e.g. rm -rf, rm -fr, rm -r -f, etc.)."""
    rm_combined_pattern = r'\brm\s+.*-(?:[a-zA-Z]*[rR][a-zA-Z]*[fF]|[a-zA-Z]*[fF][a-zA-Z]*[rR])\b'
    if re.search(rm_combined_pattern, cmd):
        return "rm -rf (recursive force remove)"

    if re.search(r'\brm\b', cmd):
        has_r = bool(re.search(r'(?:-[a-zA-Z]*[rR]|--recursive)', cmd))
        has_f = bool(re.search(r'(?:-[a-zA-Z]*[fF]|--force)', cmd))
        if has_r and has_f:
            return "rm -rf (recursive force remove)"

    return None


def check_drop_table(cmd: str) -> str | None:
    """Checks for DROP TABLE statements."""
    if re.search(r'\bDROP\s+TABLE\b', cmd, re.IGNORECASE):
        return "DROP TABLE statement"
    return None


def check_git_force_push(cmd: str) -> str | None:
    """Checks for git push with force flags (--force, -f, --force-with-lease)."""
    if re.search(r'\bgit\s+push\b.*?\b(?:--force|-f|--force-with-lease)\b', cmd, re.IGNORECASE) or \
       re.search(r'\bgit\s+push\s+.*-(?:[a-zA-Z]*f)', cmd):
        return "git push --force (force pushing to git repository)"
    return None


def check_truncate(cmd: str) -> str | None:
    """Checks for TRUNCATE statements."""
    if re.search(r'\bTRUNCATE\b', cmd, re.IGNORECASE):
        return "TRUNCATE statement"
    return None


def check_delete_without_where(cmd: str) -> str | None:
    """Checks for DELETE FROM statements without a WHERE clause."""
    matches = list(re.finditer(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE))
    if not matches:
        return None

    for match in matches:
        start_pos = match.end()
        rest = cmd[start_pos:]
        stmt_end = rest.find(';')
        stmt_text = rest[:stmt_end] if stmt_end != -1 else rest

        if not re.search(r'\bWHERE\b', stmt_text, re.IGNORECASE):
            return "DELETE FROM without a WHERE clause"

    return None


def check_command(cmd: str) -> tuple[bool, str | None]:
    """
    Evaluates command against all blocked rules.
    Returns (is_blocked, reason).
    """
    if not cmd:
        return False, None

    checks = [
        check_rm_rf,
        check_drop_table,
        check_git_force_push,
        check_truncate,
        check_delete_without_where,
    ]

    for check in checks:
        reason = check(cmd)
        if reason:
            return True, reason

    return False, None


def log_blocked_attempt(command: str, project_path: str, reason: str, log_path: str = BLOCKED_LOG_PATH) -> None:
    """Logs blocked command attempt to log_path."""
    try:
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] Project: {project_path} | Command: {command} | Reason: {reason}\n"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to log blocked attempt: {e}\n")


def get_input_payload() -> tuple[str, str]:
    """
    Extracts command and project_path from CLI args or stdin (JSON or raw text).
    Returns (command, project_path).
    """
    if len(sys.argv) > 1:
        command = sys.argv[1]
        project_path = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        return command, project_path

    raw_input = ""
    if not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()

    if raw_input:
        try:
            data = json.loads(raw_input)
            project_path = data.get("cwd") or data.get("project_path") or data.get("working_dir") or os.getcwd()

            tool_input = data.get("tool_input") or data.get("input") or data.get("parameters") or {}
            if isinstance(tool_input, dict):
                command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("script") or ""
            elif isinstance(tool_input, str):
                command = tool_input
            else:
                command = ""

            if not command:
                command = data.get("command") or data.get("cmd") or ""

            return command, project_path
        except json.JSONDecodeError:
            return raw_input, os.getcwd()

    return "", os.getcwd()


def main() -> None:
    command, project_path = get_input_payload()

    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)

    if is_blocked and reason:
        log_blocked_attempt(command, project_path, reason)

        output = {
            "status": "blocked",
            "error": f"Command blocked by pre-tool-use hook: {reason}",
            "reason": reason,
            "command": command,
            "project_path": project_path,
            "message": f"Execution of command '{command}' was blocked because it matched dangerous pattern: {reason}."
        }
        print(json.dumps(output, indent=2))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
