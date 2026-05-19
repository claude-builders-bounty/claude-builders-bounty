#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code — blocks destructive bash commands.

Place at: ~/.claude/hooks/pre_tool_use.py
Make it executable: chmod +x ~/.claude/hooks/pre_tool_use.py

Claude Code invokes this hook before executing any tool.
Respond with JSON to allow/block the tool call.
"""

import json
import re
import sys
import os
from pathlib import Path


# ── Destructive patterns ───────────────────────────────────────────
# Each entry: (regex, category, severity)
# If any regex matches the command, it's blocked.
DESTRUCTIVE_PATTERNS = [
    # File system destruction
    (r'\brm\s+(-[rRf]+\s+)*(/|~|\*)',         'rm -rf /',            'critical'),
    (r'\brm\s+(-[rRf]+\s+)*/',                 'rm -rf /',            'critical'),
    (r'\brm\s+-rf\s+',                          'rm -rf',              'high'),
    (r':(){ :\|:& };:',                         'fork bomb',           'critical'),
    (r'\bdd\s+if=',                              'dd (disk destroyer)',  'high'),
    (r'\bmkfs\.',                                'mkfs (format)',        'critical'),
    (r'>\s*/dev/sd[a-z]',                       'overwrite disk',      'critical'),
    (r'\bchmod\s+(-R\s+)?777\s+/',             'chmod 777 /',         'high'),
    (r'\bchown\s+(-R\s+)?\S+\s+/',             'chown on /',          'high'),

    # Database destruction
    (r'\bDROP\s+(TABLE|DATABASE)\b',            'DROP TABLE/DATABASE',  'critical'),
    (r'\bTRUNCATE\s+(TABLE\s+)?\S+',           'TRUNCATE TABLE',       'high'),
    (r'\bDELETE\s+FROM\s+\S+\s*$',             'DELETE without WHERE',  'high'),
    (r'\bDROP\s+SCHEMA\b',                     'DROP SCHEMA',          'critical'),
    (r'\b\.schema\s.*DROP\b',                   'SQLite schema drop',   'high'),

    # Git destruction
    (r'\bgit\s+push\s+(-f|--force)\b',         'git push --force',     'high'),
    (r'\bgit\s+push\s+origin\s+:(?!.*\bmain\b)', 'git delete branch',  'medium'),
    (r'\bgit\s+reset\s+--hard\b',              'git reset --hard',     'medium'),
    (r'\bgit\s+clean\s+-[fdx]',                'git clean',            'medium'),

    # Environment / config destruction
    (r'\bcurl.*\|\s*(ba)?sh\b',                'curl pipe bash',       'medium'),
    (r'\bwget.*\|\s*(ba)?sh\b',                'wget pipe bash',       'medium'),
    (r'>\s*~?/\.(bashrc|zshrc|profile|env)',    'overwrite rc file',    'high'),
    (r'\bshutdown\b',                           'shutdown',             'high'),
    (r'\breboot\b',                             'reboot',               'high'),
    (r'\bhalt\b',                               'halt',                 'high'),

    # Docker destruction
    (r'\bdocker\s+(system\s+)?prune\b',        'docker prune',         'medium'),
    (r'\bdocker\s+rm\s+-f\b',                  'docker rm -f',         'medium'),
    (r'\bdocker\s+volume\s+rm\b',              'docker volume rm',     'medium'),
    (r'\bdocker\s+compose\s+down\s+-v\b',      'docker compose down -v', 'medium'),

    # Package manager nukes
    (r'\bnpm\s+unpublish\b',                   'npm unpublish',        'high'),
    (r'\bpip\s+uninstall\s+-y\s+-r',           'pip uninstall all',    'high'),
    (r'\bapt(-get)?\s+purge\b',                'apt purge',            'medium'),
]

# Commands that are always safe (whitelist overrides blacklist)
SAFE_PATTERNS = [
    r'\brm\s+-rf\s+(node_modules|\.next|dist|build|__pycache__|\.cache|tmp/)',
    r'\bgit\s+push\s+--force-with-lease\b',
    r'\bgit\s+clean\s+-[fd]x?\s+(node_modules|\.next)\b',
]


def is_safe(command: str) -> bool:
    """Check if command matches a known-safe pattern."""
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command):
            return True
    return False


def check_command(command: str) -> list[dict]:
    """Check command against destructive patterns."""
    hits = []
    for pattern, name, severity in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            hits.append({
                'pattern': name,
                'severity': severity,
                'matched': pattern,
            })
    return hits


def main():
    # Read stdin — Claude Code passes tool call as JSON
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Fallback: try reading from env var
        tool_input = os.environ.get('CLAUDE_TOOL_INPUT', '{}')
        input_data = json.loads(tool_input)

    tool_name = input_data.get('tool_name', '')
    tool_input_data = input_data.get('tool_input', {})

    # Only check bash/terminal commands
    if tool_name not in ('bash', 'terminal', 'execute_command', 'shell'):
        print(json.dumps({'allow': True, 'reason': f'Not a shell command ({tool_name})'}))
        return

    command = tool_input_data.get('command', '')
    if not command:
        print(json.dumps({'allow': True, 'reason': 'No command found'}))
        return

    # Check whitelist first
    if is_safe(command):
        print(json.dumps({
            'allow': True,
            'reason': 'Safe pattern (whitelisted)',
        }))
        return

    # Check destructive patterns
    hits = check_command(command)

    if hits:
        # Format the block message
        critical_hits = [h for h in hits if h['severity'] == 'critical']
        high_hits = [h for h in hits if h['severity'] == 'high']

        details = ', '.join(h['pattern'] for h in hits)
        severity = 'critical' if critical_hits else 'high' if high_hits else 'medium'

        print(json.dumps({
            'allow': False,
            'reason': f'🚫 BLOCKED: {details}',
            'severity': severity,
            'details': hits,
            'suggestion': 'If this command is intentional, use --force flag or modify the command.'
        }))
        return

    # All clear
    print(json.dumps({'allow': True, 'reason': 'OK'}))


if __name__ == '__main__':
    main()
