#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Installed to ~/.claude/hooks/pre_tool_use.py
"""
import os
import sys
import json
import datetime
from pathlib import Path

# Destructive patterns that should ALWAYS be blocked
BLOCKED_PATTERNS = [
    # Filesystem destruction
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf $HOME",
    "rm -rf --no-preserve-root",
    "mkfs",
    "dd if=",
    "format ",
    # Git destruction
    "git push --force",
    "git push -f",
    "git reset --hard HEAD~",
    "git clean -fd",
    "git filter-branch",
    # Database destruction (use WHERE_REQUIRED_COMMANDS to allow safe queries)
    "drop table",
    "DROP TABLE",
    "drop database",
    "DROP DATABASE",
    "truncate table",
    "TRUNCATE TABLE",
    # System destruction
    "chmod -R 0",
    "chown -R ",
    "> /dev/",
    "> /etc/",
    "> /boot/",
    "wget -O /",
    "curl -o /",
    "sudo rm",
    # Docker destruction
    "docker system prune -a",
    "docker rmi -f",
    "docker container rm -f",
    # Dangerous eval
    "eval ",
    "exec ",
    "source /dev/",
]

# Commands that need a `WHERE` clause check (CRUD safety)
WHERE_REQUIRED_COMMANDS = [
    "delete from",
    "DELETE FROM",
    "update ",
    "UPDATE ",
    "truncate",
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command: str, project_path: str) -> None:
    """Log blocked command to the log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED | project={project_path} | cmd={command[:200]}\n")


def is_command_safe(command: str) -> tuple[bool, str]:
    """
    Check if a command is safe to execute.
    Returns (safe: bool, reason: str)
    """
    cmd_lower = command.lower().strip()

    # Block destructive patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in command or pattern in cmd_lower:
            return False, f"Blocked destructive pattern: '{pattern}'"

    # Check for UPDATE/DELETE without WHERE
    for cmd in WHERE_REQUIRED_COMMANDS:
        if cmd in cmd_lower:
            # Check if WHERE is present
            remaining = cmd_lower[cmd_lower.index(cmd) + len(cmd):]
            if "where" not in remaining:
                return False, f"Blocked: '{cmd.strip()}' without WHERE clause — would affect ALL rows"

    # Suspicious patterns
    suspicious = {
        ":(){ :|:& };:": "Fork bomb detected",
        "> /dev/sda": "Direct disk write",
        "chmod 0": "Setting permissions to 0",
        "mv /": "Moving root filesystem",
    }
    for pattern, reason in suspicious.items():
        if pattern in command:
            return False, f"Suspicious pattern detected: {reason}"

    return True, ""


def main():
    """Entry point for the pre-tool-use hook."""
    # Read stdin for hook payload
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IndexError):
        print(json.dumps({"isAllowed": True}))
        return

    command = payload.get("command", "")
    if not command:
        print(json.dumps({"isAllowed": True}))
        return

    # Only check BashTool executions
    tool_name = payload.get("tool", "")
    if tool_name not in ("Bash", "bash", ""):
        print(json.dumps({"isAllowed": True}))
        return

    project_path = payload.get("projectPath", os.getcwd())
    safe, reason = is_command_safe(command)

    if not safe:
        log_blocked(command, project_path)
        result = {
            "isAllowed": False,
            "message": f"⛔ SAFETY HOOK: {reason}\n\n"
                       f"Command was blocked and logged to {LOG_FILE}\n"
                       f"If you are sure about this command, run it manually "
                       f"after confirming the consequences.",
        }
    else:
        result = {"isAllowed": True}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
