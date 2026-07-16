#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before execution and blocks them.
Logs every blocked attempt with timestamp, command, and project path.

Installation:
  cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre_tool_use_block_destructive.py

Then add to ~/.claude/settings.json:
  {
    "hooks": {
      "pre_tool_use": [
        {
          "matcher": "Bash",
          "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use_block_destructive.py"}]
        }
      ]
    }
  }
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Destructive command patterns to block
BLOCKED_PATTERNS = [
    # Filesystem destruction
    (r"\brm\s+-rf?\b", "rm -rf: Recursive force delete"),
    (r"\brm\s+-fr?\b", "rm -fr: Recursive force delete"),
    (r"\brm\s+-r\b.*\*", "rm -r with wildcard: Recursive delete with glob"),
    (r"\bmkfs\b", "mkfs: Filesystem format"),
    (r"\bdd\b.*\bof=/dev/", "dd to device: Writing to block device"),
    (r"\bshred\b", "shred: Secure file deletion"),

    # Database destruction
    (r"\bDROP\s+(TABLE|DATABASE|INDEX|SCHEMA)\b", "DROP: Database object destruction"),
    (r"\bTRUNCATE\s+(TABLE\b)", "TRUNCATE: Table wipe"),
    (r"\bDELETE\s+FROM\b(?!\s*\w+\s+WHERE\b)", "DELETE without WHERE: Unconditional delete"),

    # Git destruction
    (r"\bgit\s+push\s+(-f|--force)\b", "git push --force: Force push overwrites history"),
    (r"\bgit\s+push\s+--force-with-lease\b.*--no-lease", "git push force-with-lease --no-lease: Unsafe force push"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard: Destroys uncommitted changes"),
    (r"\bgit\s+clean\s+-fd\b", "git clean -fd: Removes untracked files and directories"),

    # Process/system destruction
    (r"\bkill(?:all)?\s+-9\b.*\b(?:1|init|systemd)\b", "kill -9 on init: Killing system processes"),
    (r"\bshutdown\b", "shutdown: System shutdown"),
    (r"\breboot\b", "reboot: System reboot"),
    (r"\bhalt\b", "halt: System halt"),

    # Permission changes that could break system
    (r"\bchmod\s+-R?\s+0?000\b", "chmod 000: Removes all permissions"),
    (r"\bchown\s+-R\s+.*\s+/\s*$", "chown -R on root: Changing root ownership"),

    # Pipeline to overwrite system files
    (r"\b>\s*/etc/", "Redirect to /etc: Overwriting system config"),
    (r"\b>\s*/boot/", "Redirect to /boot: Overwriting boot files"),
    (r"\b>\s*/sys/", "Redirect to /sys: Overwriting sysfs"),

    # Fork bomb
    (r":\(\)\s*\{\s*:\|:\s*&\s*\};\s*:", "Fork bomb detected"),
]

# Compile patterns for performance
COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), desc) for p, desc in BLOCKED_PATTERNS]

# Log file path
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def get_project_path():
    """Get the current project path."""
    return os.getcwd()


def log_blocked_command(command: str, reason: str, project_path: str):
    """Log a blocked command attempt to the log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{timestamp}] BLOCKED | project={project_path} | reason={reason} | command={command[:200]}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def check_command(command: str):
    """
    Check if a command matches any blocked pattern.

    Returns:
        (is_blocked, reason) tuple
    """
    for pattern, description in COMPILED_PATTERNS:
        if pattern.search(command):
            return True, description
    return False, None


def main():
    """
    Main hook entry point.

    Reads JSON from stdin (Claude Code hook protocol), extracts the bash command,
    checks it against blocked patterns, and outputs a response.

    If blocked: exits with code 2 and prints JSON with block reason.
    If allowed: exits with code 0.
    """
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Not a valid hook input, allow the command
        sys.exit(0)

    # Extract the tool and command
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Bash commands
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = get_project_path()

    # Check against blocked patterns
    is_blocked, reason = check_command(command)

    if is_blocked:
        # Log the blocked attempt
        log_blocked_command(command, reason, project_path)

        # Output block response (Claude Code hook protocol)
        response = {
            "decision": "block",
            "reason": f"🛡️ BLOCKED: {reason}\n\nThe command was intercepted by the pre-tool-use safety hook and will not be executed.\nBlocked command: {command[:100]}\nIf this is a false positive, you can bypass by running the command directly in your terminal."
        }
        print(json.dumps(response))
        sys.exit(2)
    else:
        # Allow the command
        sys.exit(0)


if __name__ == "__main__":
    main()
