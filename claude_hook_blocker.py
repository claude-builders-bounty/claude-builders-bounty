#!/usr/bin/env python3
"""Pre-tool-use Hook: Blocks destructive commands in Claude Code."""
import re, sys

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+(-rf?|--recursive)\s+/', 'Destructive recursive delete on root'),
    (r'\brm\s+(-rf?|--recursive)\s+[^*]*\*', 'Bulk recursive delete with wildcard'),
    (r'\bmkfs\.?\w*\s+', 'Filesystem creation'),
    (r'\bdd\s+if=.*\sof=', 'Raw block device write'),
    (r'\bgit\s+push\s+(--force|-f)\b', 'Force push'),
    (r'\bgit\s+reset\s+--hard\b', 'Hard reset'),
    (r'\bgit\s+clean\s+-f[d]?\b', 'Force clean'),
    (r'\bkill\s+-9\b', 'SIGKILL'),
    (r'\bchmod\s+777\b', 'World-writable permissions'),
    (r'\bservice\s+\w+\s+stop\b', 'Service stop'),
    (r'\bdrop\s+(database|table)\b', 'Database/table deletion'),
    (r'DELETE\s+FROM', 'Unconditional table delete'),
]

def check_command(command):
    warnings = []
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Special case: DELETE FROM with WHERE clause
            if pattern == r'DELETE\s+FROM' and re.search(r'\bWHERE\b', command, re.IGNORECASE):
                continue
            warnings.append(reason)
    return warnings

def validate_tool_call(tool_name, tool_input):
    if tool_name in ('bash', 'shell', 'execute_command'):
        cmd = tool_input.get('command', '') or tool_input.get('cmd', '')
        warnings = check_command(cmd)
        if warnings:
            return {'block': True, 'reason': 'Blocked: ' + '; '.join(warnings)}
    return {'block': False}

def main():
    if sys.argv[1:] and sys.argv[1] == '--test':
        tests = {
            'rm -rf /': True, 'ls -la': False,
            'git push --force': True, 'git push origin main': False,
            'chmod 777 x': True, 'chmod 755 x': False,
            'drop database test': True, 'SELECT 1': False,
            'DELETE FROM users': True, 'DELETE FROM users WHERE id=1': False,
        }
        ok = 0
        for cmd, should_block in tests.items():
            r = check_command(cmd)
            blocked = len(r) > 0
            s = 'PASS' if blocked == should_block else 'FAIL'
            ok += 1 if blocked == should_block else 0
            if blocked != should_block:
                print(f'FAIL: "{cmd}" expected block={should_block}')
        print(f'{ok}/{len(tests)} passed')
        return 0 if ok == len(tests) else 1
    
    cmd = ' '.join(sys.argv[1:]) if sys.argv[1:] else ''
    if cmd:
        r = check_command(cmd)
        if r:
            print('BLOCKED:', '; '.join(r))
            return 1
        print('ALLOWED')
    return 0

if __name__ == '__main__':
    sys.exit(main())
