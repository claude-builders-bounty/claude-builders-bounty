#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HOOK = Path(__file__).with_name("block-destructive-bash.py")


def run(command: str, home: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/tmp/demo"}),
        text=True,
        capture_output=True,
        env={**os.environ, "HOME": home},
        check=False,
    )


with tempfile.TemporaryDirectory() as home:
    safe = run("git status --short", home)
    assert safe.returncode == 0 and safe.stderr == ""

    for command in ("rm -rf build", "DROP TABLE users", "git push --force origin main", "TRUNCATE TABLE users", "DELETE FROM users"):
        blocked = run(command, home)
        assert blocked.returncode == 2, (command, blocked)
        assert "BLOCKED:" in blocked.stderr

    allowed_delete = run("DELETE FROM users WHERE id = 1", home)
    assert allowed_delete.returncode == 0

    log_lines = (Path(home) / ".claude/hooks/blocked.log").read_text(encoding="utf-8").splitlines()
    assert len(log_lines) == 5
    assert all(json.loads(line)["project_path"] == "/tmp/demo" for line in log_lines)

print("all destructive-command hook tests passed")
