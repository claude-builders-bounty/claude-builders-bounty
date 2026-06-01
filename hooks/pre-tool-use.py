#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Intercepts bash commands before execution and blocks:
- rm -rf / or rm -rf ~
- dd if=/dev/zero (disk wipe)
- mkfs (format disk)
- chmod 777 (insecure permissions)
- :(){ :|:& };: (fork bomb)
- curl | sh (pipe to shell)
- wget | sh (pipe to shell)
- > /dev/sda (write to disk)
- shutdown/reboot/halt
- DROP TABLE/DATABASE (SQL destruction)

Usage:
  1. Save this file as ~/.claude/hooks/pre-tool-use.py
  2. chmod +x ~/.claude/hooks/pre-tool-use.py
  3. Configure in .claude/settings.json:
     {
       "hooks": {
         "pre_tool_use": {
           "bash": "python3 ~/.claude/hooks/pre-tool-use.py"
         }
       }
     }
"""

import sys
import re
import json
import os

# Destructive command patterns (regex)
BLOCKED_PATTERNS = [
    # File system destruction
    (r"rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*\s+)?/(\s|$)", "Blocked: rm -rf / (filesystem root)"),
    (r"rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*\s+)?~(/\s|$|\s)", "Blocked: rm -rf ~ (home directory)"),
    (r"rm\s+-rf\s+\*", "Blocked: rm -rf * (wildcard deletion)"),
    (r"rm\s+-rf\s+\.", "Blocked: rm -rf . (current directory)"),

    # Disk operations
    (r"dd\s+.*if=/dev/(zero|urandom|random).*of=/dev/", "Blocked: dd disk wipe"),
    (r"mkfs\.", "Blocked: mkfs (disk format)"),
    (r"mkfs\s", "Blocked: mkfs (disk format)"),
    (r">\s*/dev/sd[a-z]", "Blocked: direct disk write"),
    (r">\s*/dev/nvme", "Blocked: direct disk write"),

    # Permission abuse
    (r"chmod\s+777\s+/", "Blocked: chmod 777 on root"),
    (r"chmod\s+-R\s+777\s+/", "Blocked: chmod -R 777 on root"),
    (r"chown\s+-R\s+.*\s+/", "Blocked: chown -R on root"),

    # Fork bomb
    (r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;", "Blocked: fork bomb"),

    # Pipe to shell
    (r"curl\s+.*\|\s*(sh|bash|zsh|dash)", "Blocked: curl pipe to shell"),
    (r"wget\s+.*\|\s*(sh|bash|zsh|dash)", "Blocked: wget pipe to shell"),
    (r"curl\s+.*\|\s*(sh|bash|zsh|dash)", "Blocked: curl pipe to shell"),

    # System commands
    (r"\b(shutdown|reboot|halt|poweroff)\b", "Blocked: system shutdown"),
    (r"init\s+0", "Blocked: system shutdown"),
    (r"init\s+6", "Blocked: system reboot"),

    # SQL destruction
    (r"DROP\s+TABLE", "Blocked: DROP TABLE"),
    (r"DROP\s+DATABASE", "Blocked: DROP DATABASE"),
    (r"TRUNCATE\s+TABLE", "Blocked: TRUNCATE TABLE"),

    # Git destruction
    (r"git\s+push\s+.*--force\s+.*origin\s+main", "Blocked: force push to main"),
    (r"git\s+push\s+.*--force\s+.*origin\s+master", "Blocked: force push to master"),
    (r"git\s+clean\s+-fdx\s+/", "Blocked: git clean on root"),

    # Dangerous env manipulation
    (r"export\s+PATH\s*=\s*['"]?\s*['"]?;", "Blocked: empty PATH"),
    (r"rm\s+.*\.ssh/", "Blocked: removing SSH keys"),
    (r"rm\s+.*\.gnupg/", "Blocked: removing GPG keys"),
]

def check_command(command: str) -> tuple[bool, str]:
    """Check if a command is destructive. Returns (blocked, reason)."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def main():
    # Read the tool input from stdin or environment
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # No input, allow
        print(json.dumps({"decision": "allow"}))
        return

    # Extract the command
    command = ""
    if isinstance(input_data, dict):
        tool = input_data.get("tool", {})
        if isinstance(tool, dict):
            command = tool.get("input", {}).get("command", "")
        elif isinstance(tool, str):
            command = input_data.get("input", {}).get("command", "")

    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    # Check for destructive patterns
    blocked, reason = check_command(command)

    if blocked:
        # Block the command
        print(json.dumps({
            "decision": "block",
            "reason": reason,
            "command": command
        }))
    else:
        # Allow the command
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
