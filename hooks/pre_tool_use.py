#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Destructive Commands
Bounty #3 ($100) — claude-builders-bounty

Intercepts dangerous bash/PowerShell commands before execution.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE without WHERE,
         chmod 777, curl|bash pipes, and more.

Install (2 commands):
    copy block-destructive.py %USERPROFILE%\\.claude\\hooks\\pre_tool_use.py
    Add hook config to %USERPROFILE%\.claude\settings.json

Test:
    echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /x"}}' | python pre_tool_use.py
"""

import sys
import json
import os
import re
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "blocked.log")

DESTRUCTIVE_PATTERNS = [
    # File system destruction
    (r'\brm\s+-rf\b', 'rm -rf'),
    (r'\brm\s+-r\s+-f\b', 'rm -rf'),
    (r'\brm\s+--recursive\b', 'rm --recursive'),
    (r'\brm\s+-rf\s+/', 'rm -rf / (root deletion)'),
    (r'\bdd\s+if=', 'dd (disk destroyer)'),
    (r'\bmkfs\.', 'mkfs (format filesystem)'),
    (r'>\s*/dev/sd[a-z]', 'redirect to block device'),
    (r'\bchmod\s+777\b', 'chmod 777 (world-writable)'),
    (r'\bchmod\s+-R\s+777\b', 'chmod -R 777'),
    # Git destruction
    (r'\bgit\s+push\s+--force\b', 'git push --force'),
    (r'\bgit\s+push\s+-f\b', 'git push -f'),
    (r'\bgit\s+push\s+.*--delete\b', 'git push --delete'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard'),
    (r'\bgit\s+clean\s+-[fdx]', 'git clean (destructive)'),
    # Database destruction
    (r'\bDROP\s+TABLE\b', 'DROP TABLE', re.IGNORECASE),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE', re.IGNORECASE),
    (r'\bTRUNCATE\b', 'TRUNCATE', re.IGNORECASE),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE FROM (no WHERE clause)', re.IGNORECASE),
    # Command injection
    (r'curl.*\|\s*(ba)?sh\b', 'curl|bash pipe (RCE risk)'),
    (r'wget.*\|\s*(ba)?sh\b', 'wget|bash pipe (RCE risk)'),
    (r'curl.*\|\s*python\b', 'curl|python pipe'),
    (r'\beval\s+', 'eval (code injection)', re.IGNORECASE),
    # Environment destruction
    (r'aws\s+s3\s+rm\b', 'aws s3 rm'),
    (r'docker\s+system\s+prune\b', 'docker system prune'),
    (r'docker\s+rmi\s+-f\b', 'docker rmi -f'),
    (r'kubectl\s+delete\s+namespace\b', 'kubectl delete namespace'),
    # PowerShell destructive
    (r'\bRemove-Item\s+-Recurse\s+-Force\b', 'Remove-Item -Recurse -Force'),
    (r'\bdel\s+/[fs]\s+/q\b', 'del /f /s /q'),
]


def find_threats(command: str):
    """Scan command against all destructive patterns."""
    threats = []
    for entry in DESTRUCTIVE_PATTERNS:
        pattern = entry[0]
        label = entry[1]
        flags = entry[2] if len(entry) > 2 else 0
        if re.search(pattern, command, flags):
            threats.append((pattern, label))
    return threats


def log_block(command: str, threats: list, project_path: str):
    """Append blocked attempt to log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "matched_patterns": [t[1] for t in threats],
        "project_path": project_path or "unknown",
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        input_data = {}

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if tool_name not in ("Bash", "PowerShell"):
        print(json.dumps({"continue": True}))
        return 0

    if not command:
        print(json.dumps({"continue": True}))
        return 0

    project_path = os.getcwd()
    threats = find_threats(command)

    if not threats:
        print(json.dumps({"continue": True}))
        return 0

    log_block(command, threats, project_path)
    threat_labels = [t[1] for t in threats]

    message = (
        f"BLOCKED: Destructive command detected!\n"
        f"  Command: {command[:150]}\n"
        f"  Matched: {', '.join(threat_labels)}\n\n"
        f"  Safe alternatives:\n"
        f"  - Instead of rm -rf, move to trash first\n"
        f"  - Instead of git push --force, use --force-with-lease\n"
        f"  - Instead of DROP TABLE, back up data first\n"
        f"  - Instead of DELETE FROM without WHERE, add a WHERE clause\n\n"
        f"  Logged to: {LOG_FILE}"
    )

    print(json.dumps({
        "continue": False,
        "hookSpecificOutput": {
            "hookEventName": "pre_tool_use",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
