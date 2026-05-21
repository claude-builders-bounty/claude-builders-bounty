#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

HOOK = Path(__file__).with_name('pre-tool-use-safe-bash.py')

def run(command: str) -> int:
    payload = json.dumps({'tool_input': {'command': command}}).encode()
    return subprocess.run([sys.executable, str(HOOK)], input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode

def test_blocks_required_patterns():
    blocked = [
        'rm -rf build',
        'rm -fr build',
        'git push --force origin main',
        'psql -c "DROP TABLE users"',
        'mysql -e "TRUNCATE sessions"',
        'psql -c "DELETE FROM users"',
    ]
    for cmd in blocked:
        assert run(cmd) == 2, cmd

def test_allows_safe_commands():
    allowed = [
        'rm -r build',
        'git push origin main',
        'psql -c "DELETE FROM users WHERE id=1"',
        'echo hello',
    ]
    for cmd in allowed:
        assert run(cmd) == 0, cmd

if __name__ == '__main__':
    test_blocks_required_patterns(); test_allows_safe_commands(); print('ok')
