#!/usr/bin/env python3
import json
import subprocess
import sys

HOOK = "./destructive-command-hook.py"

cases = [
    ({"tool_input": {"command": "echo ok"}, "cwd": "/tmp/project"}, 0),
    ({"tool_input": {"command": "rm -rf build"}, "cwd": "/tmp/project"}, 2),
    ({"tool_input": {"command": "psql -c 'DROP TABLE users'"}, "cwd": "/tmp/project"}, 2),
    ({"tool_input": {"command": "git push origin main --force"}, "cwd": "/tmp/project"}, 2),
    ({"tool_input": {"command": "sqlite3 db 'DELETE FROM users;'"}, "cwd": "/tmp/project"}, 2),
    ({"tool_input": {"command": "sqlite3 db 'DELETE FROM users WHERE id=1;'"}, "cwd": "/tmp/project"}, 0),
]

for payload, expected in cases:
    proc = subprocess.run([sys.executable, HOOK], input=json.dumps(payload), text=True)
    assert proc.returncode == expected, (payload, proc.returncode, expected)

print("all destructive-command-hook checks passed")
