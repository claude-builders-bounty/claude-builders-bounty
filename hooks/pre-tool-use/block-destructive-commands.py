#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

Blocks: rm -rf /, DROP TABLE, TRUNCATE, DELETE FROM without WHERE,
        git push --force (to main/master), and other dangerous patterns.

Logs blocked attempts to ~/.claude/hooks/blocked.log with timestamp,
attempted command, and project path.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")

DESTRUCTIVE_PATTERNS = [
    # Filesystem destruction
    (r"rm\s+-rf\s+/", "rm -rf / (recursive root deletion)"),
    (r"rm\s+-rf\s+~", "rm -rf ~ (home directory deletion)"),
    (r"rm\s+-rf\s+\$HOME", "rm -rf \$HOME (home directory deletion)"),
    (r":(){ :|:& };:", "fork bomb detected"),
    (r">\s*/dev/sda", "overwriting raw block device /dev/sda"),
    (r"mkfs\.", "filesystem format command"),
    (r"dd\s+if=.*of=/dev/", "dd writing to raw block device"),

    # Database destruction
    (r"(?i)DROP\s+TABLE", "DROP TABLE (database table deletion)"),
    (r"(?i)DROP\s+DATABASE", "DROP DATABASE"),
    (r"(?i)TRUNCATE\s+(TABLE\s+)?", "TRUNCATE (table truncation)"),

    # DELETE FROM without WHERE check
    (r"(?i)DELETE\s+FROM\s+\w+(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause"),

    # Git destructive operations
    (r"git\s+push\s+--force.*(?:main|master)", "git push --force to main/master"),
    (r"git\s+push\s+-f.*(?:main|master)", "git push -f to main/master"),
    (r"git\s+reset\s+--hard", "git reset --hard"),
    (r"git\s+clean\s+-fdx", "git clean -fdx (remove all untracked files)"),

    # System commands
    (r"chmod\s+-R\s+777\s+/", "chmod -R 777 / (world-writable root)"),
    (r"chown\s+-R\s+.*\s+/", "chown -R on root filesystem"),
    (r"shutdown\s", "system shutdown command"),
    (r"reboot\s", "system reboot command"),
    (r"halt\s", "system halt command"),
]


def log_blocked(command, project_path):
    """Log a blocked command attempt to the log file."""
    os.makedirs(HOOKS_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = json.dumps({
        "timestamp": timestamp,
        "command": command,
        "project": project_path or "unknown",
    })
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as e:
        sys.stderr.write(f"Failed to write blocked log: {e}\n")


def check_command(command):
    """Check command against destructive patterns.
    Returns (is_blocked, reason) tuple."""
    if not command or not command.strip():
        return False, None

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        try:
            if re.search(pattern, command):
                return True, reason
        except re.error:
            continue
    return False, None


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid hook input JSON: {e}\n")
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    project_path = os.getcwd()

    if "cwd" in tool_input:
        project_path = tool_input["cwd"]

    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, project_path)
        msg = (
            f"BLOCKED: Destructive command detected ({reason})\n"
            f"  Command: {command}\n"
            f"  Project: {project_path}\n"
            f"  Logged to: {LOG_FILE}\n"
            f"  If you are certain this is intentional, review the command and adjust the hook config."
        )
        result = {
            "continue": False,
            "decision": "block",
            "reason": reason,
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "deny",
            },
            "systemMessage": msg,
        }
        json.dump(result, sys.stdout)
        sys.exit(2)
    else:
        result = {"continue": True}
        json.dump(result, sys.stdout)
        sys.exit(0)


if __name__ == "__main__":
    main()
