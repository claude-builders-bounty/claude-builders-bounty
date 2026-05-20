#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands."""

import sys, json, os, re
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

DANGEROUS_PATTERNS = [
    (r'\brm\s+.*-rf?\b', 'rm -rf'),
    (r'\brm\s+.*--recursive.*--force\b', 'rm --force --recursive'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE'),
    (r'\bTRUNCATE\s+(TABLE\s+)?', 'TRUNCATE'),
    (r'\bDELETE\s+FROM\s+\w+\s*;', 'DELETE FROM without WHERE'),
    (r'\bDELETE\s+FROM\s+\w+\s*$', 'DELETE FROM without WHERE'),
    (r'\bgit\s+push\s+.*--force\b', 'git push --force'),
    (r'\bgit\s+push\s+.*-f\b', 'git push -f'),
    (r'>\s*/dev/sda', 'write to block device'),
    (r':\(\)\s*\{.*:\|:.*\}', 'fork bomb'),
    (r'\bchmod\s+.*777\s+/(etc|usr|bin|sbin|lib|boot)\b', 'chmod 777 on system dir'),
]

def check_command(command):
    for pattern, danger_type in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return danger_type
    return None

def log_block(command, danger_type, project_path):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED [{danger_type}] project={project_path} cmd={command}\n")

def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"continue": True}))
        return
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    if tool_name != "Bash":
        print(json.dumps({"continue": True}))
        return
    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"continue": True}))
        return
    danger = check_command(command)
    if danger:
        project = os.getcwd()
        log_block(command, danger, project)
        message = (
            f"BLOCKED: Command matches dangerous pattern [{danger}].\n"
            f"Command: {command[:200]}\n"
            f"Log: {LOG_FILE}\n"
            f"To override: review manually and temporarily disable this hook."
        )
        print(json.dumps({"continue": False, "reason": message}))
        return
    print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
