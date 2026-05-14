#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Block Destructive Shell Commands

Intercepts Bash tool calls and blocks dangerous commands before execution.
Logs every blocked attempt to ~/.claude/hooks/blocked.log.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---

BLOCKED_PATTERNS = [
    # File destruction
    (r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)", "rm -rf: recursive force delete"),
    (r"rm\s+--recursive\s+--force", "rm --recursive --force: recursive force delete"),
    (r"shred", "shred: secure file deletion"),
    (r"mkfs", "mkfs: format filesystem"),
    (r"dd\s+.*of=/dev/", "dd to device: raw disk write"),

    # Database destruction
    (r"DROP\s+(TABLE|DATABASE|SCHEMA)", "DROP statement: permanent schema deletion"),
    (r"TRUNCATE", "TRUNCATE: delete all rows"),
    (r"DELETE\s+FROM(?!.*WHERE)", "DELETE without WHERE: deletes all rows"),
    (r"ALTER\s+TABLE.*DROP", "ALTER TABLE DROP: removes column/table"),

    # Git dangers
    (r"git\s+push\s+.*--force(?!.*--force-with-lease)", "git push --force: overwrites remote history"),
    (r"git\s+push\s+.*-f(?!.*--force-with-lease)", "git push -f: overwrites remote history"),
    (r"git\s+reset\s+--hard", "git reset --hard: discards uncommitted changes"),
    (r"git\s+clean\s+-[a-zA-Z]*f", "git clean -f: deletes untracked files"),
    (r"git\s+branch\s+-[a-zA-Z]*D", "git branch -D: force-delete branch"),

    # System dangers
    (r"chmod\s+777", "chmod 777: world-writable permissions"),
    (r"chmod\s+-R\s+777", "chmod -R 777: recursive world-writable"),
    (r">\s*/dev/sd[a-z]", "write to block device: raw disk overwrite"),
    (r"kill\s+-9\s+1", "kill -9 1: attempt to kill init"),
    (r"shutdown", "shutdown: system shutdown command"),
    (r"reboot", "reboot: system reboot command"),
    (r"init\s+0", "init 0: system halt"),

    # Network dangers
    (r"curl\s.*\|\s*(bash|sh|zsh)", "piping curl to shell: arbitrary code execution"),
    (r"wget\s.*\|\s*(bash|sh|zsh)", "piping wget to shell: arbitrary code execution"),
]

LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


def log_block(command: str, reason: str, project_path: str) -> None:
    """Log a blocked command attempt."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] BLOCKED: {reason}
  Command: {command}
  Project: {project_path}

"
    with open(LOG_FILE, "a") as f:
        f.write(entry)


def check_command(command: str) -> str | None:
    """Check if a command matches any blocked pattern. Returns reason or None."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return reason
    return None


def main() -> None:
    """Process the PreToolUse hook input from stdin."""
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # If we can't parse input, allow the command (fail open)
        print(json.dumps({"decision": "allow"}))
        return

    # Only intercept Bash tool calls
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        print(json.dumps({"decision": "allow"}))
        return

    # Extract the command
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    # Get project path for logging
    project_path = data.get("cwd", os.getcwd())

    # Check for blocked patterns
    reason = check_command(command)
    if reason:
        log_block(command, reason, project_path)
        print(json.dumps({
            "decision": "block",
            "reason": f"🚫 Command blocked by safety hook: {reason}

"
                      f"Blocked command: `{command}`

"
                      f"This command was blocked because it matches a destructive pattern. "
                      f"If you really need to run this, the user must approve it manually.

"
                      f"Logged to: {LOG_FILE}"
        }))
    else:
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
