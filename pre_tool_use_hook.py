#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook
Intercepts and blocks destructive bash/SQL commands before execution.
"""

import sys
import os
import json
import re
from datetime import datetime


def log_blocked(command: str, project_path: str):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] BLOCKED: {command} | Project: {project_path}\n"
    with open(log_file, "a") as f:
        f.write(log_entry)


def split_bash_commands(command: str) -> list[str]:
    # Split by operators: ;, &&, ||, |, and newlines
    statements = re.split(r";|&&|\|\||\||\n", command)
    return [s.strip() for s in statements if s.strip()]


def is_git_push_force(command: str) -> bool:
    cmd_lower = command.lower()
    # Check for git and push as words
    if not (re.search(r"\bgit\b", cmd_lower) and re.search(r"\bpush\b", cmd_lower)):
        return False
        
    # Check for force options
    if "--force" in cmd_lower:
        return True
    if "--force-with-lease" in cmd_lower:
        return True
        
    # Check for short flags:
    # A short flag is a token starting with a single '-' followed by letters, where one of the letters is 'f'.
    # E.g. -f, -fv, -vf
    if re.search(r"(?<!-)-[a-zA-Z]*f[a-zA-Z]*\b", cmd_lower):
        return True
        
    return False


def is_rm_rf(command: str) -> bool:
    # Check if a single bash statement represents rm -rf
    statements = split_bash_commands(command)
    for stmt in statements:
        stmt_lower = stmt.lower()
        if re.search(r"\brm\b", stmt_lower):
            # Check if both recursive (-r, -R, --recursive) and force (-f, --force) are present
            has_recursive = (
                "--recursive" in stmt_lower or
                re.search(r"(?<!-)-[a-zA-Z]*r[a-zA-Z]*\b", stmt_lower) or
                re.search(r"(?<!-)-[a-zA-Z]*R[a-zA-Z]*\b", stmt_lower)
            )
            has_force = (
                "--force" in stmt_lower or
                re.search(r"(?<!-)-[a-zA-Z]*f[a-zA-Z]*\b", stmt_lower)
            )
            if has_recursive and has_force:
                return True
    return False


def main():
    try:
        # Claude Code sends JSON to stdin of the hook
        input_data = json.load(sys.stdin)
    except Exception:
        # Fallback to allow execution if input is not JSON
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    context = input_data.get("context", {})
    project_path = context.get("project_path") or os.getcwd()

    is_blocked = False
    block_reason = ""

    # Check for rm -rf
    if is_rm_rf(command):
        is_blocked = True
        block_reason = "Destructive 'rm' command with recursive and force flags detected."

    # Check for git push --force
    elif is_git_push_force(command):
        is_blocked = True
        block_reason = "Destructive 'git push --force' command detected."

    # Check for DROP TABLE
    elif re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE):
        is_blocked = True
        block_reason = "Destructive SQL 'DROP TABLE' statement detected."

    # Check for TRUNCATE
    elif re.search(r"\bTRUNCATE\b", command, re.IGNORECASE):
        is_blocked = True
        block_reason = "Destructive SQL 'TRUNCATE' statement detected."

    # Check DELETE FROM queries without a WHERE clause
    else:
        # Split by query separator to evaluate separate statements
        queries = command.split(';')
        for query in queries:
            if re.search(r"\bDELETE\s+FROM\b", query, re.IGNORECASE) and not re.search(r"\bWHERE\b", query, re.IGNORECASE):
                is_blocked = True
                block_reason = "DELETE FROM query detected without a WHERE clause."
                break

    if is_blocked:
        log_blocked(command, project_path)
        # Print warning to stderr which Claude Code reports back to the model/user
        print(
            f"\n[SAFETY BLOCK] The command was blocked by the safety hook.\n"
            f"Reason: {block_reason}\n"
            f"Blocked command: '{command}'\n",
            file=sys.stderr
        )
        sys.exit(2)  # Exit code 2 blocks tool execution in Claude Code

    sys.exit(0)


if __name__ == "__main__":
    main()
