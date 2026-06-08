#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_blocker.py"


def run_hook(command: str, home: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    event = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/demo-project",
    }
    env = os.environ.copy()
    env["HOME"] = home
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )


def main() -> int:
    blocked = [
        "rm -rf dist",
        "psql -c 'DROP TABLE users'",
        "git push --force origin main",
        "TRUNCATE audit_log;",
        "DELETE FROM users;",
    ]
    allowed = [
        "rm -r dist",
        "git push --force-with-lease origin feature",
        "DELETE FROM users WHERE id = 1;",
        "echo hello",
    ]

    with TemporaryDirectory() as home:
        for command in blocked:
            result = run_hook(command, home)
            assert result.returncode == 2, (command, result.returncode, result.stderr)
            assert "Blocked dangerous bash command" in result.stderr

        for command in allowed:
            result = run_hook(command, home)
            assert result.returncode == 0, (command, result.returncode, result.stderr)

        result = run_hook("rm -rf dist", home, tool_name="Read")
        assert result.returncode == 0

        log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
        log_text = log_path.read_text(encoding="utf-8")
        assert "/tmp/demo-project" in log_text
        assert "rm -rf dist" in log_text

    print("pre-tool-use blocker tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
