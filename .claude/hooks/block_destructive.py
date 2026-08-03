#!/usr/bin/env python3
"""
pre_tool_use.py — Claude Code pre-tool-use hook
Blocks destructive bash commands before execution.

Bounty: #3 ($100) — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
Install: mkdir -p ~/.claude/hooks && cp this file ~/.claude/hooks/pre_tool_use.py
"""

import re, os, sys, json, datetime

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked_commands.jsonl")

BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b',       'rm -rf: recursive force delete, permanently removes files'),
    (r'\bdd\s+if=',          'dd: low-level disk write, can destroy data'),
    (r'\bmkfs\.',            'mkfs: filesystem creation, destructive'),
    (r'\bDROP\s+TABLE',      'DROP TABLE: destructive SQL operation'),
    (r'\bTRUNCATE\s+',       'TRUNCATE: destructive SQL operation'),
    (r'\bDELETE\s+FROM\s+\w+\s+(?!\s*WHERE)', 'DELETE without WHERE clause'),
    (r'\bgit\s+push\s+--force\b', 'git push --force: destructive force-push'),
    (r'\bformat\s+[A-Z]:\\\s*/q', 'format: disk formatting'),
    (r'\bchmod\s+-R\s+0',    'chmod -R 0: permission lockout on entire tree'),
    (r'>\s+/dev/sd',         'Writing directly to block device, corrupts data'),
    (r':\s*\(\s*\)\s*\{|:\s*\)\s*\|', 'Fork bomb: system crash via process exhaustion'),
    (r'\bshutdown\s+-h\s+now', 'Immediate shutdown'),
    (r'\breboot\b',          'System reboot'),
    (r'\bsudo\s+rm\s+-rf\s+/\s*$', 'sudo rm -rf /: destroy entire filesystem'),
]

def log_blocked(tool_name, command, reason):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "tool": tool_name,
        "command": command[:200],
        "reason": reason,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "unknown")
    command = os.environ.get("CLAUDE_TOOL_COMMAND", "")
    if tool_name not in ("bash", "execute", "shell", "command"):
        return
    command_str = command.strip().lower()
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            log_blocked(tool_name, command, reason)
            print("[BLOCKED] " + reason)
            print("Command: " + command[:120])
            sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
