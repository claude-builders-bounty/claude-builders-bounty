#!/usr/bin/env python3
"""Lightweight tests for the destructive-command guard."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "pre_tool_use_block_destructive.py"


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/project",
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def assert_blocked(command: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"


def assert_allowed(command: str, home: Path) -> None:
    result = run_hook(command, home)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_home:
        home = Path(temp_home)
        assert_blocked("rm -rf dist", home)
        assert_blocked("rm -fr dist", home)
        assert_blocked("git push --force origin main", home)
        assert_blocked("git push --force-with-lease origin main", home)
        assert_blocked("psql -c 'DROP TABLE users'", home)
        assert_blocked("mysql -e 'TRUNCATE sessions'", home)
        assert_blocked("psql -c 'DELETE FROM users;'", home)

        assert_allowed("rm dist/file.txt", home)
        assert_allowed("git push origin main", home)
        assert_allowed("psql -c 'DELETE FROM users WHERE id = 1;'", home)
        assert_allowed("npm test", home)

        log_file = home / ".claude" / "hooks" / "blocked.log"
        lines = log_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 7
        first = json.loads(lines[0])
        assert first["attempted_command"] == "rm -rf dist"
        assert first["project_path"] == "/tmp/project"

    print("All destructive-command guard tests passed.")


if __name__ == "__main__":
    main()
