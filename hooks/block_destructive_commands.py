#!/usr/bin/env python3
import sys, os, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Optional

DANGEROUS_PATTERNS = [
    (r'\brm\s+.*-(?:[a-zA-Z]*r[a-zA-Z]*f|[a-zA-Z]*f[a-zA-Z]*r|[rR]\s+-[fF]|[fF]\s+-[rR])\b', 'Recursive force removal (rm -rf) is blocked to prevent file loss.'),
    (r'\bDROP\s+TABLE\b', 'SQL DROP TABLE detected. Table deletion must be done manually.'),
    (r'\bgit\s+push\b.*?(?:--force|-f\b)', 'Force-pushing (git push --force) is blocked to preserve history.'),
    (r'\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_]+', 'SQL TRUNCATE detected. Table truncation is destructive.'),
]

def check_command_safety(command: str) -> Tuple[bool, Optional[str]]:
    clean = command.strip()
    match = re.search(r'\bDELETE\s+FROM\s+([a-zA-Z0-9_]+)(.*)', clean, re.IGNORECASE | re.DOTALL)
    if match:
        remainder = match.group(2)
        if not re.search(r'\bWHERE\b', remainder, re.IGNORECASE):
            return False, 'DELETE FROM without a WHERE clause is blocked to prevent table wipe.'
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, clean, re.IGNORECASE):
            return False, reason
    return True, None

def log_blocked(command: str, project_path: str, reason: str):
    log_dir = Path.home() / '.claude' / 'hooks'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'blocked.log'
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = f'[{now}] BLOCKED\n  Project: {project_path}\n  Command: {command}\n  Reason: {reason}\n------------------------------------------------------------\n'
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass

def main():
    command = ''
    project = os.getcwd()
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read().strip()
            if raw:
                try:
                    p = json.loads(raw)
                    t_input = p.get('tool_input', {})
                    command = t_input.get('command', '')
                    project = p.get('project_path', project)
                except Exception:
                    command = raw
        except Exception:
            pass
    if not command and len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
    if not command:
        sys.exit(0)
    is_safe, reason = check_command_safety(command)
    if not is_safe:
        log_blocked(command, project, reason)
        sys.stderr.write(f'\n[BLOCKED BY CLAUDE CODE SAFETY HOOK]\nCommand: {command}\nReason: {reason}\n')
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
