#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

import sys, json, re, os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

DANGEROUS_PATTERNS = [
    (r'rm\s+-rf\s', "Deleting files recursively (rm -rf)"),
    (r'DROP\s+TABLE', "Dropping database tables (DROP TABLE)"),
    (r'DROP\s+DATABASE', "Dropping entire database (DROP DATABASE)"),
    (r'git\s+push\s+.*--force', "Force pushing to git remote"),
    (r'git\s+push\s+.*-f\b', "Force pushing to git remote"),
    (r'TRUNCATE\s+(TABLE\s+)?', "Truncating database tables"),
    (r'DELETE\s+FROM\s+\w+\s*$', "DELETING without WHERE clause"),
    (r'DELETE\s+FROM\s+\w+\s*;', "DELETING without WHERE clause"),
    (r'shutdown\s+(-r|-h|now)', "Shutting down or rebooting system"),
    (r':\s*\(\)\s*\{.*:.*\}', "Obfuscated fork bomb pattern"),
    (r'chmod\s+777', "Setting world-writable permissions"),
    (r'curl.*\|\s*(ba)?sh', "Piping curl output to shell"),
    (r'wget.*-O-.*\|\s*(ba)?sh', "Piping wget output to shell"),
    (r'mkfs\.', "Formatting filesystem"),
    (r'dd\s+if=', "Raw disk write with dd"),
]

SKIP_PATTERNS = [
    r'rm\s+-rf\s+.*node_modules',
    r'rm\s+-rf\s+.*__pycache__',
    r'rm\s+-rf\s+.*\.cache',
    r'rm\s+-rf\s+.*dist',
    r'rm\s+-rf\s+.*build',
    r'rm\s+-rf\s+.*target',
    r'rm\s+-rf\s+.*\.next',
]

def load_input():
    try:
        return json.load(sys.stdin)
    except:
        return None

def log_block(command, reason, workdir):
    entry = f"[{datetime.now().isoformat()}] BLOCKED: {reason}\n"
    entry += f"  Command: {command}\n"
    entry += f"  Project: {workdir}\n"
    entry += "\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def is_skippable(command):
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, command, re.I):
            return True
    return False

def check_command(command):
    if is_skippable(command):
        return None
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.I):
            return reason
    return None

def main():
    data = load_input()
    if not data:
        sys.exit(0)
    
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    
    if tool_name.lower() != "bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    workdir = tool_input.get("workdir", os.getcwd())
    reason = check_command(command)
    
    if reason:
        log_block(command, reason, workdir)
        result = {
            "decision": "block",
            "reason": (
                f"DESTRUCTIVE COMMAND BLOCKED: {reason}\n"
                f"The command was: `{command}`\n"
                f"Logged to: {LOG_FILE}\n"
                f"If you are CERTAIN this is safe, use --dangerously-bypass-hook flag."
            )
        }
        print(json.dumps(result))
        sys.exit(2)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
