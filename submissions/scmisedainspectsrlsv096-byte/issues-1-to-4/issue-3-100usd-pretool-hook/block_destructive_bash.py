#!/usr/bin/env python3
"""Bounty #3 ($100): PreToolUse Hook that blocks destructive Bash commands in Claude Code.

Reads JSON tool input from stdin (Claude Code PreToolUse format), inspects 'command',
and exits with code 2 (blocking execution and returning reason to Claude) if a destructive
command pattern is detected.
"""
import json, re, sys

DESTRUCTIVE_PATTERNS = [
    (r'(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+-[a-zA-Z]*[rR][a-zA-Z]*f[a-zA-Z]*\s+(/|\*|~|\$HOME|/root|/etc|/usr|/var)\b', 'Recursive forced deletion of critical root/home path'),
    (r'(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+-[a-zA-Z]*f[a-zA-Z]*[rR][a-zA-Z]*\s+(/|\*|~|\$HOME|/root|/etc|/usr|/var)\b', 'Recursive forced deletion of critical root/home path'),
    (r'--no-preserve-root', 'rm --no-preserve-root is prohibited'),
    (r'\bmkfs(?:\.[a-z0-9]+)?\b', 'Filesystem formatting (mkfs) is prohibited'),
    (r'\bdd\b(?=.*\bof=/dev/(?:sd|nvme|vd|hd|mmcblk|loop|disk))', 'Raw block device overwrite via dd is prohibited'),
    (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;?\s*:', 'Fork bomb detected'),
    (r'\bgit\s+push\b(?=.*(?:--force|-f\b))(?=.*\b(?:main|master|prod|production)\b)', 'Force-pushing to main/master/production branch is blocked'),
    (r'\bgit\s+reset\s+--hard\b', 'Uncommitted work loss risk: git reset --hard is blocked without explicit backup'),
    (r'\b(?:DROP\s+DATABASE|DROP\s+TABLE|TRUNCATE\s+TABLE)\b', 'Destructive SQL DDL statement detected'),
    (r'\bchmod\s+-R\s+777\s+/', 'Recursive world-writable permission change on root path is blocked'),
]

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool_name = payload.get('tool_name') or payload.get('tool') or ''
    if tool_name.lower() not in ('bash', 'run_command', 'shell', ''):
        return 0
    tool_input = payload.get('tool_input') or payload.get('input') or {}
    cmd = tool_input.get('command') or tool_input.get('CommandLine') or ''
    if not isinstance(cmd, str) or not cmd.strip():
        return 0

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            msg = {
                'decision': 'block',
                'reason': f'[Security PreToolUse Hook] Blocked destructive command ({reason}): {cmd[:120]}',
            }
            print(json.dumps(msg))
            print(msg['reason'], file=sys.stderr)
            return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
