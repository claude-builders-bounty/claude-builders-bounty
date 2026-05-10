#!/usr/bin/env python3
import json
import subprocess
import sys


HOOK = "safe-bash-hook/block_destructive_bash.py"


def run(command):
    payload = {
        "cwd": "/tmp/example",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


blocked = [
    "rm -rf build",
    "rm -fr build",
    "DROP TABLE users",
    "git push --force origin main",
    "git push --force-with-lease origin main",
    "TRUNCATE users",
    "DELETE FROM users",
]

allowed = [
    "git status --short",
    "rm -r build",
    "DELETE FROM users WHERE id = 1",
    "echo hello",
]

for command in blocked:
    result = run(command)
    assert result.returncode == 2, f"expected block for {command!r}, got {result.returncode}"
    assert "Blocked unsafe Bash command" in result.stderr

for command in allowed:
    result = run(command)
    assert result.returncode == 0, f"expected allow for {command!r}, got {result.returncode}"

print("safe bash hook tests passed")
