#!/usr/bin/env python3
'''Claude Code PreToolUse safety hook - blocks destructive bash commands.
Reads tool-use JSON from stdin. Exits 0 to allow, exits 2 to block.
Blocked attempts logged as JSONL to ~/.claude/hooks/blocked.log.
'''
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / '.claude' / 'hooks' / 'blocked.log'

RULES = [
    # Destructive filesystem
    (r'(?:^|[;&|])\s*rm\s+(?:-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*|-rf|-fr)(?:\s|$)', 'rm -rf — irreversible deletion'),
    (r'(?:^|[;&|])\s*rm\s+-r\s+-f\b', 'rm -r -f — recursive force delete'),
    # Destructive git
    (r'\bgit\s+push\s+(--force|-f)\b(?!.*--lease)', 'git push --force — overwrites remote history'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard — discards uncommitted changes'),
    # Database destruction
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'DROP — irreversible data loss'),
    (r'\bTRUNCATE\s+(?:TABLE\s+)?\w+', 'TRUNCATE — removes all rows'),
    (r'\bDELETE\s+FROM\s+\w+\s*;?\s*$', 'DELETE FROM without WHERE — mass data deletion'),
    # Security risks
    (r'\bchmod\s+.*777\b', 'chmod 777 — world-writable permissions'),
    (r'curl\s+.*\|\s*(ba)?sh\b', 'curl pipe to shell — potential RCE'),
    (r'wget\s+.*\s*-O\s*-\s*\|\s*(ba)?sh\b', 'wget pipe to shell — potential RCE'),
]

def check(cmd):
    for pat, label in RULES:
        if re.search(pat, cmd, re.IGNORECASE):
            return label
    return None

def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        p = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if p.get('tool_name') not in (None, 'Bash', 'bash'):
        return 0
    ti = p.get('tool_input') or {}
    cmd = ti.get('command', '') if isinstance(ti, dict) else str(ti)
    if not cmd:
        return 0
    reason = check(cmd)
    if not reason:
        return 0
    ts = datetime.now(timezone.utc).isoformat()
    proj = p.get('cwd') or p.get('project_path') or os.getcwd()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        json.dump({'ts': ts, 'project': proj, 'command': cmd, 'reason': reason}, f, ensure_ascii=False)
        f.write('\n')
    sys.stderr.write(
        f'⚠️  BLOCKED: {reason}\n'
        f'  project: {proj}\n'
        f'  command: {cmd[:120]}\n'
        f'  logged: {LOG}\n'
        f'  tip: Use safer alternatives (--force-with-lease, mv instead of rm -rf, etc.)\n'
    )
    return 2

if __name__ == '__main__':
    sys.exit(main())
