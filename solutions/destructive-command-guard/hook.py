#!/usr/bin/env python3
"""Claude Code PreToolUse Bash guard. Conservative by design."""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

DANGEROUS = (
    (re.compile(r'(?<![\w])rm\s+(?:(?:-[\w]*r[\w]*\s+[^\n;]*?-[\w]*f)|(?:-[\w]*f[\w]*\s+[^\n;]*?-[\w]*r)|(?:-[\w]*[rf][\w]*[rf][\w]*)|(?:--recursive\s+--force)|(?:--force\s+--recursive))\b', re.I), 'forced recursive deletion'),
    (re.compile(r'\brm\s+(?:(?:-r|--recursive)\s+(?:-f|--force)|(?:-f|--force)\s+(?:-r|--recursive))(?=\s|$)', re.I), 'forced recursive deletion'),
    (re.compile(r'\bDROP\s+TABLE\b', re.I), 'DROP TABLE'),
    (re.compile(r'\bTRUNCATE(?:\s+TABLE)?\b', re.I), 'TRUNCATE'),
    (re.compile(r'\bgit\s+push\b[^\n;|]*?(?:--force(?:-with-lease|-if-includes)?\b|(?:^|\s)-f(?:\s|$))', re.I), 'force push'),
    (re.compile(r'\bDELETE\s+FROM\s+[^;\n]*', re.I), 'unqualified DELETE FROM'),
)

def check(command):
    for pattern, reason in DANGEROUS:
        for match in pattern.finditer(command):
            if reason == 'unqualified DELETE FROM' and re.search(r'\bWHERE\b', re.sub(r'/\*.*?\*/|--[^\n]*', '', match.group(), flags=re.S), re.I):
                continue
            return reason
    return None

def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError):
        print('Safety hook: malformed input; refusing execution', file=sys.stderr)
        return 2
    if payload.get('tool_name') not in (None, 'Bash'):
        return 0
    command = payload.get('tool_input', {}).get('command', '')
    if not isinstance(command, str):
        print('Safety hook: invalid command input', file=sys.stderr)
        return 2
    reason = check(command)
    if reason is None:
        return 0
    log = Path.home() / '.claude' / 'hooks' / 'blocked.log'
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a', encoding='utf-8') as out:
            out.write(json.dumps({'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(), 'command': command, 'project_path': payload.get('cwd', os.getcwd()), 'reason': reason}) + '\n')
    except OSError as exc:
        print(f'Safety hook: logging failed: {exc}', file=sys.stderr)
    print(f'BLOCKED: {reason}. Revise the Bash command to avoid destructive operations.', file=sys.stderr)
    return 2

if __name__ == '__main__':
    sys.exit(main())
