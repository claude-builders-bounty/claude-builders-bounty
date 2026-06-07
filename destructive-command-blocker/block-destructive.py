#!/usr/bin/env python3
"""Claude Code pre-tool-use hook to block destructive bash commands."""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

DANGEROUS_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b',
     "Recursive force remove (rm -rf)"),
    (r'\brm\s+-rf\s+/',
     "Deleting root filesystem (rm -rf /)"),
    (r'\bdd\s+if=.*\s+of=/dev/(sd|hd|nvme|xvd|vd)',
     "Overwriting block device with dd"),
    (r'>\s*/dev/(sd|hd|nvme|xvd|vd)',
     "Redirecting to block device"),
    (r':\(\)\s*\{\s*:\|:&\s*\}\s*;:',
     "Fork bomb detected"),
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b',
     "SQL DROP statement"),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+',
     "SQL TRUNCATE statement"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?!WHERE)',
     "SQL DELETE without WHERE clause"),
    (r'\bgit\s+push\s+.*(--force|--force-with-lease)\b',
     "Git force push"),
    (r'\bgit\s+reset\s+--hard\b',
     "Git hard reset"),
    (r'\bgit\s+checkout\s+--\s+\.?\b',
     "Git checkout -- (discard all changes)"),
    (r'\bgit\s+clean\s+(-[a-zA-Z]*[fd][a-zA-Z]*)+\b',
     "Git clean with force"),
    (r'\bchmod\s+(-R\s+)?777\b',
     "World-writable permissions (chmod 777)"),
    (r'\bchown\s+-R\s+\S+\s+/\b',
     "Recursive chown on root"),
    (r'\bsystemctl\s+(disable|mask)\s+(ssh|sshd|network|systemd)',
     "Disabling critical system service"),
    (r'\bcurl\s+.*\|\s*(bash|sh|zsh)\b',
     "Curl pipe to shell"),
    (r'\bwget\s+.*-O\s*-\s*\|\s*(bash|sh|zsh)\b',
     "Wget pipe to shell"),
    (r'\bexport\s+PATH\s*=\s*[\"'"'"'`]?[.]',
     "Overwriting PATH with current directory"),
]


def block_command(command, project_path):
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {"blocked": True, "reason": reason, "pattern": pattern}
    return {"blocked": False}


def log_block(command, reason, project_path):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "reason": reason,
        "project": project_path,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        allow = json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }})
        print(allow)
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }}))
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd", os.getcwd())

    if not command:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }}))
        sys.exit(0)

    result = block_command(command, cwd)

    if result["blocked"]:
        log_block(command, result["reason"], cwd)
        msg = (
            f"BLOCKED: {result['reason']}\n"
            f"  Command: {command}\n"
            f"  Logged to: {LOG_FILE}"
        )
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg
        }}))
        sys.stderr.write(msg + "\n")
        sys.exit(0)

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow"
    }}))
    sys.exit(0)


if __name__ == "__main__":
    main()
