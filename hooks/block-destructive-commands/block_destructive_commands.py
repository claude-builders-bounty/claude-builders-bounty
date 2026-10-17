#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Intercepts and prevents execution of dangerous system and database commands.
"""

import sys
import os
import json
import re
from datetime import datetime

# Path to audit log
CLAUDE_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(CLAUDE_DIR, "blocked.log")

def is_rm_rf(command: str) -> bool:
    """Checks if command invokes rm with both recursive and force flags."""
    # Direct regex match for common combined forms
    if re.search(r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF]|\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*[rR]", command):
        return True
    
    # Token-based check for separated flags like 'rm -r -f', 'rm --recursive --force'
    parts = command.split()
    for idx, part in enumerate(parts):
        if part == "rm" or part.endswith("/rm"):
            has_r = False
            has_f = False
            for arg in parts[idx + 1:]:
                if arg.startswith("-") and not arg.startswith("--"):
                    if "r" in arg.lower():
                        has_r = True
                    if "f" in arg.lower():
                        has_f = True
                elif arg in ["--recursive", "-r", "-R"]:
                    has_r = True
                elif arg in ["--force", "-f"]:
                    has_f = True
            if has_r and has_f:
                return True
    return False


def log_blocked(command: str, project_path: str, reason: str):
    """Logs blocked commands to ~/.claude/hooks/blocked.log with ISO timestamp."""
    try:
        os.makedirs(CLAUDE_DIR, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] BLOCKED: {command} | PROJECT: {project_path} | REASON: {reason}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")


def check_command(command: str) -> tuple[bool, str]:
    """
    Evaluates a command string against known dangerous patterns.
    Returns: (is_blocked: bool, explanation: str)
    """
    # 1. Check rm -rf
    if is_rm_rf(command):
        return True, "Recursive force removal ('rm -rf') can cause irreversible system or file loss."

    # 2. Check DROP TABLE/DATABASE/SCHEMA/VIEW
    if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\b", command, re.IGNORECASE):
        return True, "SQL DROP statement detected. This will destroy tables or schemas permanently."

    # 3. Check git push --force
    if re.search(r"\bgit\s+push\s+.*(--force|-f|\+[a-zA-Z0-9_\-\/]+)\b", command, re.IGNORECASE):
        return True, "Forced git push ('git push --force' / '-f') detected. This rewrites remote history and can overwrite colleagues' commits."

    # 4. Check TRUNCATE
    if re.search(r"\bTRUNCATE(\s+TABLE)?\b", command, re.IGNORECASE):
        return True, "SQL TRUNCATE statement detected. This deletes all records without transaction rollback."

    # 5. Check DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", command, re.IGNORECASE):
            return True, "SQL DELETE statement without a WHERE clause detected. This will purge the entire table."

    return False, ""


def main():
    # Read tool input from stdin (Claude Code hook standard protocol)
    input_data = ""
    if not sys.stdin.isatty():
        input_data = sys.stdin.read().strip()

    command_to_check = ""
    tool_name = "bash"

    if input_data:
        try:
            parsed = json.loads(input_data)
            tool_name = parsed.get("tool_name", "bash")
            tool_input = parsed.get("tool_input", {})
            if isinstance(tool_input, dict):
                command_to_check = tool_input.get("command", "")
            elif isinstance(tool_input, str):
                command_to_check = tool_input
        except json.JSONDecodeError:
            # Raw string command passed
            command_to_check = input_data
    elif len(sys.argv) > 1:
        command_to_check = " ".join(sys.argv[1:])

    # Only inspect bash / command execution tools
    if tool_name not in ["bash", "execute_command", "run_command", "sh"] and not command_to_check:
        sys.exit(0)

    if not command_to_check:
        sys.exit(0)

    project_path = os.getcwd()
    is_blocked, reason = check_command(command_to_check)

    if is_blocked:
        log_blocked(command_to_check, project_path, reason)
        error_message = (
            f"\n⛔ [SAFETY HOOK INTERCEPTED DANGEROUS COMMAND]\n"
            f"Command: {command_to_check}\n"
            f"Location: {project_path}\n"
            f"Reason: {reason}\n"
            f"Audit log updated: {LOG_FILE}\n\n"
            f"Action was aborted to protect repository integrity. "
            f"If this operation is truly intended, run it manually with explicit user confirmation.\n"
        )
        sys.stderr.write(error_message)
        # Non-zero exit code informs Claude Code to block execution
        sys.exit(2)

    # Allowed command
    sys.exit(0)


if __name__ == "__main__":
    main()
