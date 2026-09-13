#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive.py"


def run(payload: dict) -> tuple[str, int]:
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
    )
    return proc.stdout.strip(), proc.returncode


def assert_deny(cmd: str) -> None:
    out, code = run({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": "/tmp/p"})
    assert code == 0, (cmd, out)
    data = json.loads(out)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny", (cmd, data)


def assert_allow(cmd: str) -> None:
    out, code = run({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": "/tmp/p"})
    assert code == 0 and out == "", (cmd, out)


def main() -> None:
    # blocked
    for c in [
        "rm -rf /tmp/x",
        "sudo rm -fr ./build",
        "DROP TABLE users;",
        "TRUNCATE sessions",
        "git push --force origin main",
        "git push -f origin HEAD",
        "DELETE FROM users",
        "DELETE FROM users;",
    ]:
        assert_deny(c)

    # allowed
    for c in [
        "ls -la",
        "rm file.txt",
        "git push origin main",
        "DELETE FROM users WHERE id = 1",
        "SELECT * FROM users",
        "echo DROP TABLE is a string",  # still matches DROP TABLE — wait, this WOULD block
    ]:
        if "DROP TABLE" in c and c.startswith("echo"):
            # literal DROP TABLE anywhere in bash string is blocked by design (fail-closed)
            assert_deny(c)
        else:
            assert_allow(c)

    print("OK — all safeguard tests passed")


if __name__ == "__main__":
    main()
