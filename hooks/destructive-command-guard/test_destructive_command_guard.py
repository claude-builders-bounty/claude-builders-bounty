#!/usr/bin/env python3
import importlib.util
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).with_name('destructive-command-guard.py')
spec = importlib.util.spec_from_file_location('guard', SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

blocked = [
    'rm -rf /tmp/build',
    'rm -fr dist',
    'psql -c "DROP TABLE users"',
    'git push --force origin main',
    'git push -f',
    'TRUNCATE sessions',
    'DELETE FROM users',
]
allowed = [
    'rm -r /tmp/build',
    'git push origin main',
    'SELECT * FROM users',
    'DELETE FROM users WHERE id = 1',
    'echo hello',
]

for command in blocked:
    assert guard.blocked_reason(command), command
for command in allowed:
    assert guard.blocked_reason(command) is None, command

payload = {
    'hook_event_name': 'PreToolUse',
    'tool_name': 'Bash',
    'cwd': '/tmp/example-project',
    'tool_input': {'command': 'DELETE FROM users'},
}
run = subprocess.run([str(SCRIPT)], input=json.dumps(payload), text=True, capture_output=True, check=True)
out = json.loads(run.stdout)
assert out['hookSpecificOutput']['hookEventName'] == 'PreToolUse'
assert out['hookSpecificOutput']['permissionDecision'] == 'deny'
assert 'DELETE FROM' in out['hookSpecificOutput']['permissionDecisionReason']

safe_payload = payload | {'tool_input': {'command': 'echo safe'}}
safe = subprocess.run([str(SCRIPT)], input=json.dumps(safe_payload), text=True, capture_output=True, check=True)
assert safe.stdout == ''
