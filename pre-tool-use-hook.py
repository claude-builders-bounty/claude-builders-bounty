#!/usr/bin/env python3
# Claude Code pre-tool-use hook: block destructive bash commands
# Place in: ~/.claude/hooks/pre-tool-use.py
import os
import re
import sys
from datetime import datetime

BLOCKED_PATTERNS = [
    r'^\s*rm\s+(-rf|-fr)\b',           # rm -rf, rm -fr
    r'^\s*rm\s+/-rf\b',                # rm -rf /
    r'\bDROP\s+TABLE\b',               # DROP TABLE
    r'\bTRUNCATE\s+TABLE\b',           # TRUNCATE TABLE
    r'\bDELETE\s+FROM\b(?!\s+.*WHERE)',  # DELETE FROM without WHERE
    r'\bgit\s+push\s+--force\b',       # git push --force
    r'\bgit\s+push\s+-f\b',            # git push -f
    r'\bformat\s+[\(/]',               # format disk/partition
    r'\bdd\s+if=.*of=/dev/',            # dd to device
    r'\bsh\s+-c\s+rm\s+-rf',          # sh -c rm -rf
]

BLOCKED_PATTERNS_COMPILED = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

LOG_FILE = os.path.expanduser('~/.claude/hooks/blocked.log')

def log_blocked(command, project_path):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_line = f'[{timestamp}] BLOCKED: {command} | Project: {project_path}'
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line + chr(10))
    return f'**Command blocked:** {command}
**Reason:** This command matches a security rule (destructive operation).
**Log:** {LOG_FILE}'

def check_command(cmd):
    for pattern in BLOCKED_PATTERNS_COMPILED:
        if pattern.search(cmd):
            return True, pattern.pattern
    return False, None

def main():
    if len(sys.argv) < 2:
        return 0
    cmd = ' '.join(sys.argv[1:])
    blocked, matched = check_command(cmd)
    if blocked:
        project = os.getcwd()
        msg = log_blocked(cmd, project)
        print(msg, file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
