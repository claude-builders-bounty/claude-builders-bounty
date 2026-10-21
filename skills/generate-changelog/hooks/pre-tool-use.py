#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
Intercepts and blocks destructive bash and SQL commands before execution.
"""

import sys
import os
import re
import json
from datetime import datetime

BLOCKED_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force)\b', 'Destructive file deletion (rm -rf)'),
    (r'\bgit\s+push\s+.*\b(-f|--force)\b', 'Force-pushing to git remote (git push --force)'),
    (r'\bDROP\s+TABLE\b', 'Destructive SQL: DROP TABLE'),
    (r'\bTRUNCATE(\s+TABLE)?\b', 'Destructive SQL: TRUNCATE TABLE'),
    (r'\bDELETE\s+FROM\s+[a-zA-Z0-9_]+(\s*;)?\s*$', 'Unbounded SQL deletion: DELETE FROM without a WHERE clause')
]

LOG_DIR = os.path.expanduser('~/.claude/hooks')
LOG_FILE = os.path.join(LOG_DIR, 'blocked.log')

def log_blocked(cmd, reason, project_path):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = f"[{timestamp}] REASON: {reason} | PATH: {project_path} | COMMAND: {cmd}\n"
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[Warning] Failed to write to blocked.log: {e}\n")

def check_command(cmd_text, cwd="."):
    for pattern, desc in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_text, re.IGNORECASE):
            log_blocked(cmd_text, desc, cwd)
            sys.stderr.write(f"\n🚨 [CLAUDE CODE SAFETY HOOK] EXECUTION BLOCKED!\n")
            sys.stderr.write(f"Reason: {desc}\n")
            sys.stderr.write(f"Attempted Command: {cmd_text}\n")
            sys.stderr.write(f"Project Path: {cwd}\n")
            sys.stderr.write(f"Logged to: {LOG_FILE}\n\n")
            sys.exit(1)

def main():
    # Hook receives tool input via stdin (JSON) or CLI arguments
    cwd = os.getcwd()
    raw_input = ""
    
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()
        
    if not raw_input:
        sys.exit(0)
        
    # Check if raw input is JSON from Claude Code
    try:
        data = json.loads(raw_input)
        tool_name = data.get('tool', '').lower()
        tool_input = data.get('input', {})
        
        if tool_name in ['bash', 'run_command', 'execute_command']:
            cmd = tool_input.get('command', '') or tool_input.get('cmd', '')
            check_command(cmd, cwd)
    except Exception:
        # Plain command line string
        check_command(raw_input, cwd)
        
    sys.exit(0)

if __name__ == '__main__':
    main()
