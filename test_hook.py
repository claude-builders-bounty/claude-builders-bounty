import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("block_destructive_bash.py")


def run(command):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/test-project"
    }

    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True
    )

    return result.stdout.strip()


blocked = [
    "rm -rf /tmp/test",
    "rm -fr /tmp/test",
    "rm -r -f /tmp/test",
    "git push --force origin main",
    "git push -f origin main",
    "DROP TABLE users",
    "TRUNCATE TABLE users",
    "DELETE FROM users"
]

allowed = [
    "rm file.txt",
    "npm test",
    "git status",
    "git push origin main",
    "git push --force-with-lease origin main",
    "DELETE FROM users WHERE id=1",
    "echo rm -rf"
]

for command in blocked:
    assert run(command), "NOT BLOCKED: " + command

for command in allowed:
    assert not run(command), "FALSE BLOCK: " + command

print("PASS:", len(blocked) + len(allowed), "tests")
