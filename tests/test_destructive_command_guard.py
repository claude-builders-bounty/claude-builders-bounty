#!/usr/bin/env python3
"""Local tests for the destructive command guard hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / ".claude" / "hooks" / "destructive_command_guard.py"


def run_hook(command: str, *, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    env["HOME"] = run_hook.temp_home  # type: ignore[attr-defined]
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str) -> None:
    result = run_hook(command)
    assert result.returncode == 2, (command, result.returncode, result.stderr)
    assert "Blocked destructive Bash command" in result.stderr, result.stderr


def assert_allowed(command: str, *, tool_name: str = "Bash") -> None:
    result = run_hook(command, tool_name=tool_name)
    assert result.returncode == 0, (command, result.returncode, result.stderr)
    assert result.stderr == "", result.stderr


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_home:
        run_hook.temp_home = temp_home  # type: ignore[attr-defined]

        blocked = [
            "rm -rf build",
            "sudo /bin/rm -fr /tmp/demo",
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'TRUNCATE audit_log'",
            "git push --force origin main",
            "git push -f origin main",
            "git -C ../repo push --force origin main",
            "sudo -n git push --force origin main",
            "sudo -n git -C ../repo push -f origin main",
            "mysql -e 'DELETE FROM users;'",
        ]
        allowed = [
            "echo hello",
            "rm -ri build",
            "git push origin main",
            "python3 -m pytest",
            "mysql -e 'DELETE FROM users WHERE id = 1;'",
            "echo 'DROP TABLE users'",
            "grep 'DELETE FROM' schema.sql",
            "cat notes.sql",
            "cat <<'SQL'\nDROP TABLE users;\nDELETE FROM users;\nSQL",
        ]

        for command in blocked:
            assert_blocked(command)
        for command in allowed:
            assert_allowed(command)
        assert_allowed("rm -rf build", tool_name="Read")

        log_path = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == len(blocked), lines
        first_entry = json.loads(lines[0])
        assert set(first_entry) == {"timestamp", "attempted_command", "project_path", "reason"}
        assert first_entry["attempted_command"] == blocked[0]
        assert first_entry["project_path"] == "/tmp/example-project"

    print("All destructive command guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
