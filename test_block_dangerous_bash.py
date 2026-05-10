#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

HOOK = Path(__file__).parent / "hooks" / "block-dangerous-bash.py"


def run(command: str):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp/project"}
    return subprocess.run(["python3", str(HOOK)], input=json.dumps(payload), text=True, capture_output=True, check=False)


blocked = [
    "rm -rf build",
    "psql -c 'DROP TABLE users'",
    "git push --force origin main",
    "sqlite3 app.db 'TRUNCATE sessions'",
    "sqlite3 app.db 'DELETE FROM users;'",
]
allowed = [
    "rm -r build",
    "git push origin main",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 1;'",
    "echo hello",
]

for command in blocked:
    result = run(command)
    assert result.returncode == 0, (command, result.stderr)
    assert '"permissionDecision": "deny"' in result.stdout, (command, result.stdout)

for command in allowed:
    result = run(command)
    assert result.returncode == 0, (command, result.stderr)
    assert result.stdout.strip() == "", (command, result.stdout)

print("ok")
