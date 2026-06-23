#!/usr/bin/env python3
"""Pre-tool-use hook that blocks destructive bash commands.

Claude Code hooks format: https://docs.anthropic.com/en/docs/claude-code/hooks
Install: cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
"""
import re, os, sys, datetime

BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', 'rm -rf (recursive delete)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE (destructive schema change)'),
    (r'\bTRUNCATE\b', 'TRUNCATE (data wipe)'),
    (r'\bDELETE\s+FROM\b(?!\s+\w+\s+WHERE)', 'DELETE FROM without WHERE'),
    (r'\bgit\s+push\s+--force\b', 'git push --force (history rewrite)'),
    (r'\bgit\s+push\s+origin\s+\+?[^ ]+\b(?!.*--force)', 'Non-force push with +ref'),
    (r'\bFORMAT\s+', 'FORMAT (drive/database format)'),
    (r'\bdd\s+if=', 'dd if= (raw device write)'),
    (r'\bmkfs\.', 'mkfs (filesystem creation)'),
    (r'\bsudo\s+rm\b', 'sudo rm (privileged deletion)'),
]

LOG_FILE = os.path.expanduser('~/.claude/hooks/blocked.log')

def check_command(command: str) -> tuple[bool, str]:
    for pattern, desc in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, desc
    return False, ''

def main():
    command = os.environ.get('HERMES_TOOL_INPUT', sys.stdin.read() if not sys.stdin.isatty() else '')
    
    blocked, reason = check_command(command)
    if blocked:
        log_entry = f"[{datetime.datetime.now().isoformat()}] BLOCKED: {reason}\n  Command: {command[:200]}\n"
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
        print(f"❌ BLOCKED: {reason}")
        print(f"   Logged to: {LOG_FILE}")
        sys.exit(1)

if __name__ == '__main__':
    main()
