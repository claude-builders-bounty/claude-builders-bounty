#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Bash Command Interceptor
Intercepts dangerous bash commands (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE).
Exits with code 2 to halt execution and logs attempts to ~/.claude/hooks/blocked.log.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def is_destructive(command: str) -> tuple[bool, str]:
    """
    Evaluates command against destructive safety rules.
    Returns (is_blocked, reason).
    """
    cmd = command.strip()

    # Pattern 1: rm -rf (handles flags in any order e.g. rm -rf, rm -fr, rm -r -f)
    if re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*', cmd, re.I):
        return True, "Recursive force file deletion (rm -rf)"

    # Pattern 2: DROP TABLE
    if re.search(r'\bDROP\s+TABLE\b', cmd, re.I):
        return True, "Destructive SQL table drop (DROP TABLE)"

    # Pattern 3: git push --force (or -f)
    if re.search(r'\bgit\s+push\b.*(\s--force\b|\s-f\b)', cmd, re.I):
        return True, "Force pushing to git remote (git push --force)"

    # Pattern 4: TRUNCATE
    if re.search(r'\bTRUNCATE\b', cmd, re.I):
        return True, "Destructive SQL table truncation (TRUNCATE)"

    # Pattern 5: DELETE FROM without WHERE clause
    if re.search(r'\bDELETE\s+FROM\b', cmd, re.I):
        if not re.search(r'\bWHERE\b', cmd, re.I):
            return True, "Unbounded SQL deletion (DELETE FROM without WHERE clause)"

    return False, ""


def log_blocked_attempt(project_path: str, command: str, reason: str):
    """
    Logs blocked attempt to ~/.claude/hooks/blocked.log
    with: timestamp, attempted command, project path.
    """
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"

    timestamp = datetime.now().isoformat()
    log_entry = (
        f"[{timestamp}] | Project: {project_path} | "
        f"Command: {command} | Reason: {reason}\n"
    )

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[Hook Warning] Failed to write to {log_file}: {e}\n")


def main():
    project_path = os.getcwd()
    command = ""

    # Strategy 1: Read JSON passed on stdin by Claude Code PreToolUse
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                payload = json.loads(stdin_data)
                project_path = payload.get("cwd", project_path)
                tool_input = payload.get("tool_input", {})
                command = tool_input.get("command", "")
        except Exception:
            pass

    # Strategy 2: CLI argument fallback for manual or automated testing
    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    # If no command detected, allow execution
    if not command:
        sys.exit(0)

    blocked, reason = is_destructive(command)

    if blocked:
        log_blocked_attempt(project_path, command, reason)

        explanation = (
            f"❌ [SECURITY GUARDRAIL] Bash command blocked: '{command}'\n"
            f"Reason: {reason}\n"
            f"This command matches a destructive pattern forbidden by the safety hook.\n"
            f"Incident logged to ~/.claude/hooks/blocked.log\n"
        )
        sys.stderr.write(explanation)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
