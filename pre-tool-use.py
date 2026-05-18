#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: block destructive bash commands.
Install: ln -s /path/to/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
"""
import sys
import json
import re
import os
from datetime import datetime, timezone

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
BLOCKED_LOG = os.path.join(HOOK_DIR, "blocked.log")

# Patterns that are ALWAYS dangerous, no WHERE clause saves them
ALWAYS_DANGEROUS = [
    (re.compile(r'^\s*rm\s+-rf\s+'), "rm -rf deletes directory trees recursively"),
    (re.compile(r'^\s*git\s+push\s+--force'), "git push --force rewrites remote history"),
    (re.compile(r'^\s*TRUNCATE\s+'), "TRUNCATE removes all rows from a table"),
]

# Patterns that are dangerous only when no WHERE clause is present
DANGEROUS_WITH_CONDITION = [
    (re.compile(r'\bDROP\s+TABLE\b(?!\s+IF\s+EXISTS)'), "DROP TABLE removes entire table structure and data"),
    (re.compile(r'\bDELETE\s+FROM\b(?!\s+WHERE)'), "DELETE FROM without WHERE deletes all rows"),
]

# Commands that are safe to let through (whitelist helper)
SAFE_PREFIXES = [
    'echo', 'ls', 'pwd', 'cd ', 'git status', 'git log', 'git diff',
    'cat ', 'head', 'tail', 'grep', 'find', 'which', 'whoami',
    'mkdir', 'touch', 'cp ', 'mv ', 'chmod', 'chown',
]


def is_likely_safe(command: str) -> bool:
    """Quick pre-check to avoid false positives on safe commands."""
    stripped = command.strip().split('\n')[0]  # only check first line
    for prefix in SAFE_PREFIXES:
        if stripped.startswith(prefix) or stripped.startswith(prefix + ' '):
            return True
    return False


def check_command(command: str) -> tuple[bool, str]:
    """Returns (blocked, reason)."""
    if is_likely_safe(command):
        return False, ""

    # Check ALWAYS_DANGEROUS patterns
    for pattern, reason in ALWAYS_DANGEROUS:
        if pattern.search(command):
            return True, reason

    # Check conditional-dangerous patterns
    for pattern, reason in DANGEROUS_WITH_CONDITION:
        if pattern.search(command):
            # Double-check: scan for WHERE clause (not perfect but good enough)
            upper = command.upper()
            # Simple heuristic: does it have a WHERE before any banned keyword?
            # We already matched DROP TABLE or DELETE FROM, now check for WHERE
            if re.search(r'\bWHERE\b', command, re.IGNORECASE):
                return False, ""  # has WHERE, appears safe
            return True, reason

    return False, ""


def log_blocked(timestamp: str, command: str, project_path: str, reason: str):
    """Append blocked attempt to blocked.log."""
    entry = (
        f"[{timestamp}] BLOCKED | Project: {project_path}\n"
        f"  Reason: {reason}\n"
        f"  Command: {command[:200]}...\n"
        if len(command) > 200 else
        f"[{timestamp}] BLOCKED | Project: {project_path}\n"
        f"  Reason: {reason}\n"
        f"  Command: {command}\n"
    )
    with open(BLOCKED_LOG, "a") as f:
        f.write(entry + "\n")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"allow": True}))
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    project_path = os.environ.get("CLAUDE_PROJECT_PATH", "unknown")

    if tool_name != "Bash":
        print(json.dumps({"allow": True}))
        return

    command = tool_input.get("command", "")
    blocked, reason = check_command(command)

    if blocked:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_blocked(timestamp, command, project_path, reason)

        # Block the command by returning an error in the hook response
        error_msg = (
            f"🔒 HOOK BLOCKED: {reason}\n"
            f"This command was intercepted by the pre-tool-use security hook.\n"
            f"Project: {project_path}\n"
            f"If you believe this is a false positive, you can bypass by running "
            f"the command directly in your terminal."
        )
        print(json.dumps({
            "allow": False,
            "error": error_msg,
            "block_reason": reason,
        }))
        return

    print(json.dumps({"allow": True}))


if __name__ == "__main__":
    main()
