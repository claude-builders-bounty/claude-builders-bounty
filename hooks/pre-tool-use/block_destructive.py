#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook: Block Destructive Bash Commands.
Bounty submission for claude-builders-bounty issue #3.
"""

import sys
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

def is_rm_rf(cmd: str) -> bool:
    """Detects any variant of rm -rf / rm -fr / rm -r -f / rm --recursive --force."""
    if not re.search(r"\brm\b", cmd):
        return False
    # Combined flags like -rf, -fr, -rfi, -vrf
    if re.search(r"(?:^|\s)-[a-zA-Z]*[rR][a-zA-Z]*[fF]|-[a-zA-Z]*[fF][a-zA-Z]*[rR]", cmd):
        return True
    # Separate flags: -r ... -f or --recursive ... --force
    has_r = bool(re.search(r"(?:^|\s)(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)\b", cmd))
    has_f = bool(re.search(r"(?:^|\s)(-[a-zA-Z]*[fF][a-zA-Z]*|--force)\b", cmd))
    return has_r and has_f

def is_git_force_push(cmd: str) -> bool:
    """Detects git push --force / git push -f / git push +branch."""
    if not re.search(r"\bgit\s+push\b", cmd):
        return False
    return bool(re.search(r"(?:^|\s)(--force|-f|\+[\w/]+)\b", cmd))

def is_drop_database_or_table(cmd: str) -> bool:
    """Detects DROP TABLE / DROP DATABASE / DROP SCHEMA."""
    return bool(re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\b", cmd, re.IGNORECASE))

def is_truncate_table(cmd: str) -> bool:
    """Detects TRUNCATE [TABLE]."""
    return bool(re.search(r"\bTRUNCATE(\s+TABLE)?\s+[a-zA-Z0-9_.\"`]+\b", cmd, re.IGNORECASE))

def is_delete_without_where(cmd: str) -> bool:
    """Detects DELETE FROM without a WHERE clause."""
    if re.search(r"\bDELETE\s+FROM\b", cmd, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", cmd, re.IGNORECASE):
            return True
    return False

def check_command(command: str) -> tuple[bool, str]:
    """
    Evaluates command against destructive rules.
    Returns (is_blocked, reason).
    """
    cmd = command.strip()

    if is_rm_rf(cmd):
        return True, "Recursive force removal (`rm -rf`) is blocked to prevent accidental deletion of critical files."

    if is_git_force_push(cmd):
        return True, "Git force pushing (`git push --force`) is blocked to prevent overwriting remote commit history."

    if is_drop_database_or_table(cmd):
        return True, "Executing `DROP TABLE / DATABASE` is blocked to prevent irreversible data loss."

    if is_truncate_table(cmd):
        return True, "Executing `TRUNCATE TABLE` is blocked to prevent bulk data deletion."

    if is_delete_without_where(cmd):
        return True, "Executing `DELETE FROM` without a `WHERE` clause is blocked because it deletes all records."

    return False, ""

def get_log_file_path() -> Path:
    """Returns ~/.claude/hooks/blocked.log, ensuring directory exists."""
    claude_hooks_dir = Path.home() / ".claude" / "hooks"
    claude_hooks_dir.mkdir(parents=True, exist_ok=True)
    return claude_hooks_dir / "blocked.log"

def log_blocked_attempt(command: str, reason: str, project_path: str, log_file: Path | None = None):
    """Logs timestamp, command, and project path to blocked.log."""
    target_log = log_file or get_log_file_path()
    now_iso = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{now_iso}] PATH: {project_path} | REASON: {reason} | COMMAND: {command.strip()}\n"
    try:
        with open(target_log, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def extract_command_from_payload() -> str:
    """Extracts command from stdin JSON, stdin string, or argv."""
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])

    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if not raw_input:
                return ""
            try:
                data = json.loads(raw_input)
                if isinstance(data, dict):
                    if "input" in data and isinstance(data["input"], dict) and "command" in data["input"]:
                        return str(data["input"]["command"])
                    if "command" in data:
                        return str(data["command"])
            except json.JSONDecodeError:
                pass
            return raw_input
        except Exception:
            pass

    return ""

def main():
    command = extract_command_from_payload()
    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)
    if is_blocked:
        project_path = os.getcwd()
        log_blocked_attempt(command, reason, project_path)

        sys.stderr.write("\n" + "=" * 70 + "\n")
        sys.stderr.write("🛑 [BLOCKED BY CLAUDE CODE PRE-TOOL-USE SECURITY HOOK]\n")
        sys.stderr.write(f"Reason: {reason}\n")
        sys.stderr.write(f"Blocked Command: {command}\n")
        sys.stderr.write("Logged to: ~/.claude/hooks/blocked.log\n")
        sys.stderr.write("=" * 70 + "\n\n")

        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
