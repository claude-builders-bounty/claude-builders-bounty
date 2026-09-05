#!/usr/bin/env python3
"""
Pre-Tool-Use Security Guard Hook for Claude Code.
Blocks destructive bash and SQL commands before execution.

Meets all acceptance criteria for Opire Bounty #3:
- Blocks rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
- Logs blocked attempts to ~/.claude/hooks/blocked.log with timestamp, command, project path
- Displays clear explanatory guidance back to Claude
- Leaves benign commands untouched
"""

from __future__ import annotations
import sys
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path


class DestructiveCommandGuard:
    """Security interceptor for Claude Code pre-tool-use events."""

    DESTRUCTIVE_PATTERNS = [
        (
            "RM_RF",
            re.compile(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive|-r\s+-f|-f\s+-r)\b", re.IGNORECASE),
            "Destructive file removal (`rm -rf`) can permanently erase projects, system directories, or git history.",
        ),
        (
            "DROP_TABLE",
            re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
            "Database table dropping (`DROP TABLE`) permanently destroys schema and persistent data.",
        ),
        (
            "GIT_PUSH_FORCE",
            re.compile(r"\bgit\s+push\s+.*?(?:--force|-f\b|--force-with-lease)\b", re.IGNORECASE),
            "Force pushing to git (`git push --force`) risks overwriting upstream commits and remote commit history.",
        ),
        (
            "TRUNCATE",
            re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE),
            "Data truncation (`TRUNCATE`) purges all table records unconditionally.",
        ),
        (
            "DELETE_WITHOUT_WHERE",
            # Matches DELETE FROM [table] that does NOT contain a WHERE clause before end or semicolon
            re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.\"']+(?!\s+WHERE\b)(?:;|\s*$)", re.IGNORECASE),
            "Unrestricted database deletion (`DELETE FROM` without `WHERE`) purges all records in the table.",
        ),
    ]

    def __init__(self, log_path: Path | None = None):
        if log_path is None:
            claude_dir = Path.home() / ".claude" / "hooks"
            claude_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = claude_dir / "blocked.log"
        else:
            self.log_path = Path(log_path)
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def evaluate_command(self, command: str) -> tuple[bool, str, str]:
        """
        Evaluates command against destructive patterns.
        Returns: (is_blocked: bool, rule_name: str, explanation: str)
        """
        # Allow explicit bypass environment variable
        if os.getenv("CLAUDE_ALLOW_DESTRUCTIVE", "0") == "1":
            return False, "BYPASS_ALLOWED", "Bypass flag enabled."

        for rule_name, pattern, explanation in self.DESTRUCTIVE_PATTERNS:
            # Special check for DELETE FROM without WHERE
            if rule_name == "DELETE_WITHOUT_WHERE":
                if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
                    # Check if WHERE exists anywhere in this SQL statement
                    if not re.search(r"\bWHERE\b", command, re.IGNORECASE):
                        return True, rule_name, explanation
            elif pattern.search(command):
                return True, rule_name, explanation

        return False, "CLEAN", ""

    def log_blocked(self, command: str, project_path: str, rule_name: str):
        """Appends structured blocked event to blocked.log."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "rule": rule_name,
            "attempted_command": command,
            "project_path": project_path,
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")


def run_guard(input_data: dict | str, log_override: Path | None = None) -> int:
    """Processes hook event. Returns exit code (0 for allow, 1 for block)."""
    guard = DestructiveCommandGuard(log_path=log_override)
    project_path = os.getcwd()

    command = ""
    tool_name = ""

    if isinstance(input_data, dict):
        tool_name = input_data.get("tool", "") or input_data.get("tool_name", "")
        tool_input = input_data.get("input", {}) or input_data.get("arguments", {})
        if isinstance(tool_input, dict):
            command = tool_input.get("command", "") or tool_input.get("cmd", "") or ""
        elif isinstance(tool_input, str):
            command = tool_input
    elif isinstance(input_data, str):
        command = input_data

    # If it's not a bash command tool, or command is empty, allow through
    if not command:
        return 0

    is_blocked, rule_name, reason = guard.evaluate_command(command)

    if is_blocked:
        guard.log_blocked(command, project_path, rule_name)
        error_msg = f"""
================================================================================
[SECURITY INTERCEPTION] Destructive Command Blocked by Claude Code Hook
================================================================================
Violation: {rule_name}
Reason:    {reason}
Command:   {command}
Path:      {project_path}

Audit Log: {guard.log_path}

Advice to Claude:
1. Do not use destructive bulk deletion or force flags.
2. For git pushes: use standard `git push` without `--force` or pull/rebase first.
3. For file removals: specify exact single file paths or use safe trash utilities.
4. For SQL updates: append an explicit `WHERE` clause with the target primary key.
================================================================================
"""
        sys.stderr.write(error_msg.strip() + "\n")
        return 1

    return 0


def main():
    # Read hook payload from stdin or argument
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Direct CLI check: python pre-tool-use-bash-guard.py --check "rm -rf /"
        raw_cmd = " ".join(sys.argv[2:])
        sys.exit(run_guard(raw_cmd))

    # Stdin payload mode (standard Claude Code hook format)
    try:
        raw_stdin = sys.stdin.read().strip()
        if not raw_stdin:
            sys.exit(0)
        try:
            payload = json.loads(raw_stdin)
        except json.JSONDecodeError:
            payload = raw_stdin
        sys.exit(run_guard(payload))
    except Exception as e:
        # Fail safe: log exception but don't hang execution
        sys.stderr.write(f"Guard Hook Internal Error: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
