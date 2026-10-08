#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook
Intercepts and blocks destructive bash commands before execution.
Logs blocked attempts to ~/.claude/hooks/blocked.log with timestamp, command, and project path.
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

def get_log_file_path() -> Path:
    """Return ~/.claude/hooks/blocked.log path."""
    home_dir = Path.home()
    hooks_dir = home_dir / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "blocked.log"

def log_blocked_attempt(command: str, project_path: str, reason: str):
    """Log blocked attempt with timestamp, command, and project path."""
    try:
        log_path = get_log_file_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] [BLOCKED] Project: {project_path}\n"
            f"  Command: {command}\n"
            f"  Reason:  {reason}\n"
            f"{'-' * 80}\n"
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[Security Hook Warning] Failed to write to blocked.log: {e}\n")

def check_command(command_str: str) -> tuple[bool, str]:
    """
    Check if command matches any destructive pattern:
    - rm -rf
    - DROP TABLE
    - git push --force
    - TRUNCATE
    - DELETE FROM without WHERE clause
    """
    if not command_str:
        return False, ""

    cmd = command_str.strip()

    # 1. Recursive force deletion: rm -rf, rm -fr, rm -r -f, rm --recursive --force
    rm_pattern = (
        r'(?:^|\s|;|&&|\|\|)rm\s+.*?-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r)\b|'
        r'(?:^|\s|;|&&|\|\|)rm\s+.*?(?:-r\b|-R\b|--recursive\b).*?(?:-f\b|--force\b)|'
        r'(?:^|\s|;|&&|\|\|)rm\s+.*?(?:-f\b|--force\b).*?(?:-r\b|-R\b|--recursive\b)'
    )
    if re.search(rm_pattern, cmd, re.IGNORECASE):
        return True, "Recursive force deletion ('rm -rf') detected. High risk of unrecoverable data loss."

    # 2. SQL DROP TABLE
    if re.search(r'\bdrop\s+table\b', cmd, re.IGNORECASE):
        return True, "Database destruction ('DROP TABLE') detected."

    # 3. Forced git push
    git_force_pattern = r'\bgit\s+push\b.*(?:\s--force\b|\s-f\b|\s--force-with-lease\b)'
    if re.search(git_force_pattern, cmd, re.IGNORECASE):
        return True, "Forced git push ('git push --force') detected. Risks overwriting shared branch history."

    # 4. SQL TRUNCATE
    if re.search(r'\btruncate\s+(?:table\s+)?[\w`"\'\.]+', cmd, re.IGNORECASE):
        return True, "Database truncation ('TRUNCATE TABLE') detected."

    # 5. SQL DELETE FROM without WHERE clause
    del_match = re.search(r'\bdelete\s+from\s+[\w`"\'\.]+(.*)', cmd, re.IGNORECASE | re.DOTALL)
    if del_match:
        clause_remainder = del_match.group(1).strip()
        # If there is no 'WHERE' keyword in the remainder
        if not re.search(r'\bwhere\b', clause_remainder, re.IGNORECASE):
            return True, "Unbounded table deletion ('DELETE FROM' without WHERE clause) detected."

    return False, ""

def parse_input():
    """
    Parse tool name, command, and project path from stdin (JSON) or CLI arguments.
    Compatible with Claude Code hook protocols.
    """
    tool_name = "Bash"
    command = ""
    project_path = os.getcwd()

    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                payload = json.loads(stdin_data)
                tool_name = payload.get("tool_name") or payload.get("tool", "Bash")
                tool_input = payload.get("tool_input") or payload.get("input", {})
                if isinstance(tool_input, dict):
                    command = tool_input.get("command", "")
                elif isinstance(tool_input, str):
                    command = tool_input
                project_path = payload.get("project_path") or payload.get("cwd") or os.getcwd()
        except Exception:
            command = stdin_data

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        command = os.getenv("CLAUDE_TOOL_COMMAND", "")
    project_path = os.getenv("CLAUDE_PROJECT_PATH", project_path)

    return tool_name, command, project_path

def main():
    tool_name, command, project_path = parse_input()

    if tool_name and tool_name.lower() not in ("bash", "sh", "shell", "terminal"):
        sys.exit(0)

    if not command:
        sys.exit(0)

    is_dangerous, reason = check_command(command)

    if is_dangerous:
        log_blocked_attempt(command, project_path, reason)

        sys.stderr.write(
            f"\n🚨 [CLAUDE CODE SECURITY HOOK - COMMAND BLOCKED]\n"
            f"The following destructive bash command was intercepted and prevented from executing:\n"
            f"  Command:      {command}\n"
            f"  Reason:       {reason}\n"
            f"  Project Path: {project_path}\n"
            f"  Logged to:    ~/.claude/hooks/blocked.log\n\n"
            f"Action Required: If this operation is intentional, please execute it manually outside Claude Code.\n\n"
        )
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
