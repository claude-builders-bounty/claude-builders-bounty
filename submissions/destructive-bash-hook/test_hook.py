"""Test destructive bash hook patterns."""
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "block_destructive.py"


def run(cmd: str) -> int:
    payload = f'{{"tool_input": {{"command": "{cmd}"}}, "cwd": "/test/project"}}'
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
    )
    return r.returncode


assert run("ls -la") == 0
assert run("rm -rf /") == 2
assert run("git push --force origin main") == 2
assert run("DROP TABLE users") == 2
assert run("echo hello") == 0
print("all tests passed")
