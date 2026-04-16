#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Place at: ~/.claude/hooks/pre-tool-use/destructive_guard.py
"""

import json
import re
import sys

BLOCKED_PATTERNS = [
    (r'\brm\s+(-\S*f\S*|-\S*r\S*\s+-\S*f\S*|-rf|-fr)\b', 'rm -rf (recursive force delete)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
    (r'\bTRUNCATE\b', 'TRUNCATE'),
    (r'\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE)', 'DELETE FROM without WHERE'),
    (r'\bgit\s+push\s+.*--force\b', 'git push --force'),
    (r'\bgit\s+push\s+.*-f\b', 'git push -f'),
    (r'\bdd\s+if=', 'dd if= (disk write)'),
    (r'>\s*/dev/sd[a-z]', 'write to block device'),
    (r'\bchmod\s+-R\s+777\b', 'chmod -R 777'),
    (r'\bsudo\s+rm\b', 'sudo rm'),
    (r':\(\)\s*\{.*:\|:&\s*\}', 'fork bomb'),
]

CONFIRMATION_REQUIRED = [
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard'),
    (r'\bgit\s+clean\s+-fd?\b', 'git clean -f'),
]


def check_command(command: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason)."""
    cmd_upper = command.upper()
    cmd_normalized = ' '.join(command.split())

    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_normalized, re.IGNORECASE):
            return True, f"BLOCKED: {description}\nCommand: {command!r}\n\nThis command is potentially destructive and has been prevented by the safety hook."

    return False, ""


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    is_blocked, reason = check_command(command)

    if is_blocked:
        response = {
            "action": "block",
            "message": reason,
        }
        print(json.dumps(response))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
