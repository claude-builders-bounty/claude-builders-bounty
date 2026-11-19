#!/usr/bin/env python3
"""pre-tool-use.py — Claude Code hook that blocks destructive bash commands.

Place at ~/.claude/hooks/pre-tool-use.py and chmod +x.
Reads the tool call from stdin as JSON:
    {"tool": "bash", "arguments": {"command": "rm -rf /tmp"}}
Exit code 1 + stderr message = blocked. Exit code 0 = allowed.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_LOG = Path.home() / '.claude' / 'hooks' / 'blocked.log'

PATTERNS = [
    (re.compile(r'\brm\s+(-[a-zA-Z]*[fR][a-zA-Z]*\s+)+[\w\.~/\*]', re.I), 'rm -rf / recursive force delete'),
    (re.compile(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+[\w\.~/\*]', re.I), 'rm with recursive flag'),
    (re.compile(r'\bDROP\s+TABLE\b', re.I), 'DROP TABLE'),
    (re.compile(r'\bDROP\s+DATABASE\b', re.I), 'DROP DATABASE'),
    (re.compile(r'\bTRUNCATE\b', re.I), 'TRUNCATE'),
    (re.compile(r'\bDELETE\s+FROM\b(?=[^;]*(;|$))', re.I), 'DELETE FROM without WHERE'),
    (re.compile(r'\bgit\s+push\s+(--force|\-f\b)', re.I), 'git push --force'),
    (re.compile(r'\bgit\s+push\s+--delete\b', re.I), 'git push --delete'),
    (re.compile(r'\bgit\s+reset\s+--hard\b', re.I), 'git reset --hard'),
    (re.compile(r'\bchmod\s+-R\s+777\b', re.I), 'chmod -R 777'),
    (re.compile(r'\bmkfs\b', re.I), 'mkfs'),
    (re.compile(r'\bdd\s+if=/dev/zero\b', re.I), 'dd if=/dev/zero'),
]


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0  # Not JSON; don't block.

    arguments = payload.get('arguments') or {}
    command = arguments.get('command') if isinstance(arguments, dict) else None
    if not command:
        return 0

    # Log and block matching patterns.
    blocked = None
    for pattern, name in PATTERNS:
        if pattern.search(command):
            blocked = name
            break

    # DELETE FROM without WHERE (separate check for accuracy)
    if blocked is None:
        m = re.search(r'\bDELETE\s+FROM\s+[^\s;]+', command, re.I)
        if m:
            tail = command[m.end():]
            if not re.search(r'\bWHERE\b', tail, re.I):
                blocked = 'DELETE FROM without WHERE'

    if not blocked:
        return 0

    # Gather timestamp + attempted command + project path.
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = {
        'timestamp': ts,
        'command': command,
        'project_path': os.getcwd(),
        'reason': blocked,
    }
    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BLOCKED_LOG.open('a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass  # Log failure must not block the block decision.

    # Surface why to the model via stderr (hooks contract).
    sys.stderr.write(
        'Blocked by pre-tool-use hook: "' + command + '"\n'
        + 'Reason: ' + blocked + '\n'
        + 'This command would be destructive/irreversible. '
        + 'Re-consider: is there a safe, reversible alternative?\n'
    )
    return 1


if __name__ == '__main__':
    sys.exit(main())
